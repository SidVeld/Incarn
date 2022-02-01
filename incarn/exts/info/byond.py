import yaml
from numpy import uint16
from pathlib import Path
from socket import socket
from typing import Optional

from discord import Embed
from discord.ext.commands import Cog, Context, group

from incarn.bot import IncarnBot
from incarn.log import get_logger

log = get_logger(__name__)


class Byond(Cog):
    """Honk."""

    def __init__(self, bot: IncarnBot) -> None:
        self.bot = bot
        self.fetch_servers()

    @classmethod
    def fetch_servers(self) -> None:
        """Fetches servers dict from special file."""
        server_file = Path("incarn/resources/info/ss13.yml")
        servers: dict = yaml.load(server_file.open(encoding="utf-8"), Loader=yaml.FullLoader)
        self.servers = servers

    @classmethod
    def is_server_supported(self, server_tag: str, request_type: str) -> bool:
        """Checks is server supported by bot."""
        self.fetch_servers()

        for server in self.servers.values():
            tags: list = server["tags"]
            requests: dict = server["fields"]
            if server_tag.lower() in tags and request_type in list(requests.keys()):
                return True
        return False

    @classmethod
    def get_ip_port(self, server_tag: str) -> tuple[str, int]:
        self.fetch_servers()
        for server in self.servers.values():
            if server_tag.lower() in server["tags"]:
                return server["ip"], server["port"]

    @classmethod
    def get_server_name_color(self, server_tag: str):
        self.fetch_servers()
        for server in self.servers.values():
            if server_tag.lower() in server["tags"]:
                return server["name"], server["color"]

    @classmethod
    def get_server_fields(self, server_tag: str, request_type: str):
        self.fetch_servers()
        for server in self.servers.values():
            if server_tag.lower() in server["tags"]:
                return server["fields"][request_type]

    @classmethod
    def get_from_byond(self, ip: str, port: int, message: str) -> Optional[bytes]:
        client = socket()
        try:
            client.connect((ip, port))
            client.send(self.build_message_bytearray(message))
            response = client.recv(1460)
            client.close()
        except Exception as error:
            log.error(f"{ip}:{port} - {error}")
            client.close()
            return None
        return response

    @staticmethod
    def build_message_bytearray(message: str) -> bytearray:
        """Builds message's bytearray."""
        length = uint16(len(message) + 6)
        msg = bytearray()
        msg.extend(b"\x00\x83")
        msg.append(length >> 8)
        msg.append((length << 8) >> 8)
        msg.extend(b'\x00\x00\x00\x00\x00')
        msg.extend(bytes(message, encoding="utf_8"))
        msg.extend(b'\x00')
        return msg

    @staticmethod
    def decode(data):
        data = "".join([chr(x) for x in data[5:-1]])
        data = data.replace("%3a", ":")
        data = data.replace("+", " ")
        data = data.split("&")
        ndat = {"other": list(), "player": list()}

        for i in data:
            j = i.split("=")

            if(j[0][:6] == "player" and j[0][6] != "s"):
                ndat["player"].append(j[1])
            elif(len(j)-1):
                ndat[j[0]] = j[1]
            else:
                ndat["other"].append(j[0])

        return ndat

    @group(name="ss13")
    async def ss13(self, ctx: Context) -> None:
        """nigger"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @ss13.command(name="servers")
    async def servers_list(self, ctx: Context) -> None:
        """Sends suppoted server list."""
        self.fetch_servers()

        embed = Embed(
            title="Servers",
            description="You can get information about this servers.\n\n",
            colours=0x0984e3
        )

        for server in self.servers.values():
            name: str = server["name"]
            tags: list = server["tags"]
            line = f"- **{name}**: " + ", ".join(tags) + "\n"
            embed.description += line

        await ctx.send(embed=embed)

    @ss13.command(name="status")
    async def ss13_server_status(self, ctx: Context, server_tag: str) -> None:
        """Sends server status."""
        if self.is_server_supported(server_tag, "status") is False:
            await ctx.send("Sorry, but this is not supported for this server.")
            return

        ip, port = self.get_ip_port(server_tag)
        response = self.get_from_byond(ip, port, "status")

        if response is None:
            await ctx.send("Something goes wrong. I didn't recieved data from server.")
            return

        data = self.decode(response)
        fields: dict = self.get_server_fields(server_tag, "status")
        name, color = self.get_server_name_color(server_tag)
        embed = Embed(title=name, colour=color)

        for field in fields.values():
            embed.add_field(name=field["name"], value=data[field["key"]], inline=field["inline"])

        await ctx.send(embed=embed)


def setup(bot: IncarnBot) -> None:
    """Load the Byond cog."""
    bot.add_cog(Byond(bot))
