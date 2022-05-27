from pathlib import Path
from discord import Embed
import yaml
import socket
import struct
import urllib.parse

from discord.ext.commands import Cog, Context, group

from incarn.bot import IncarnBot
from incarn.log import get_logger

log = get_logger(__name__)

TOPIC_PACKET_ID = b'\x83'
TOPIC_RESPONSE_FLOAT = b'\x2a'
TOPIC_RESPONSE_STRING = b'\x06'


class Byond(Cog):
    """Byond-related commands. Honk."""

    def _get_servers(self):
        config = Path("incarn/resources/info/ss13.yml")
        data: dict = yaml.safe_load(config.open())
        return data

    def _is_server_supported(self, server_name: str):
        servers = self._get_servers()
        for server in servers.values():
            if server_name.lower() in server["aliases"]:
                return True
        return False

    def _get_server_config(self, server_name: str):
        servers = self._get_servers()
        for server in servers.values():
            if server_name.lower() in server["aliases"]:
                return server

    def _build_embed(self, server_config: dict, data: dict, embed_type: str):
        embed = Embed()
        embed.title = server_config["name"]
        embed.colour = server_config["color"]
        fields: dict = server_config["embeds"][embed_type]
        for field in fields.values():
            embed.add_field(
                name=field["name"],
                value=" ".join(data[field["key"]]),
                inline=field["inline"]
            )
        return embed

    def _send_query(self, address: str, port: int, query: str):

        if len(query) == 0 or query[0] != '?':
            queryString = '?' + query
        else:
            queryString = query

        # Header:
        # - pad byte
        # - packetId (0x83)
        # - big-endian uint16_t packet-size
        # - pad byte
        packetSize = len(queryString) + 6
        if packetSize >= (2 ** 16 - 1):
            raise Exception('query string too big, max packet size exceeded.')
        packet = struct.pack('>xcH5x', TOPIC_PACKET_ID, packetSize) + bytes(queryString, encoding='utf8') + b'\x00'

        sock = socket.create_connection((address, port))
        sock.settimeout(10)
        sock.send(packet)

        # Response has a 5-byte header, which has a length attribute inside it to
        # tell us how big the response actually is. (Allegedly)

        recv_header = sock.recv(5)
        recvPacketId, content_len, response_type = struct.unpack('>xcHc', recv_header)
        if recvPacketId != TOPIC_PACKET_ID:
            # How strange. Are we perhaps talking to something that isn't a BYOND server?
            sock.close()
            raise Exception(f"Incorrect packet-ID received in response. Expecting 0x83, received {recvPacketId}")

        data = ""
        if response_type == TOPIC_RESPONSE_STRING:
            content_len -= 2
        if response_type == TOPIC_RESPONSE_FLOAT:
            content_len -= 1

        response = sock.recv(content_len)
        if len(response) < content_len:
            raise Exception(f"Truncated response: {str(len(response))} of {str(content_len)}")

        sock.close()
        if response_type == TOPIC_RESPONSE_STRING:
            data = urllib.parse.parse_qs(str(response, encoding='utf8'), keep_blank_values=True)

        elif response_type == TOPIC_RESPONSE_FLOAT:
            # Float type response, where the data returned is a floating point value.
            data = struct.unpack('<f', response)[0]

        else:
            # No idea what response *this* is, but maybe it's something
            # specific to a codebase we're not used to.
            data = response

        return (response_type, data)

    @group(name="ss13")
    async def ss13(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @ss13.command(name="status")
    async def ss13_status(self, ctx: Context, server_name: str):
        """Sends server's status topic."""
        if self._is_server_supported(server_name) is False:
            return await ctx.send("This server is not supported!")

        server_config = self._get_server_config(server_name)
        response_type, data = self._send_query(
            server_config["address"],
            server_config["port"],
            "?status"
        )
        embed = self._build_embed(server_config, data, "status")

        await ctx.send(embed=embed)


def setup(bot: IncarnBot) -> None:
    """Load the Byond cog."""
    bot.add_cog(Byond(bot))
