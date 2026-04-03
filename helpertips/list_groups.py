"""
list_groups.py — Lista grupos e canais do Telegram para configuração.

Conecta com suas credenciais, mostra todos os grupos/canais disponíveis
com nome, ID e tipo. Permite escolher qual grupo monitorar e salva
automaticamente no .env.

Uso direto:
    python -m helpertips.list_groups

Uso integrado (chamado pelo listener quando TELEGRAM_GROUP_ID está vazio):
    from helpertips.list_groups import selecionar_grupo
    group_id = await selecionar_grupo(client)
"""

import os
import re

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat

console = Console()


async def listar_grupos(client: TelegramClient) -> list[dict]:
    """Retorna lista de grupos/canais do Telegram do usuário."""
    grupos = []
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        if isinstance(entity, (Channel, Chat)):
            tipo = "canal" if getattr(entity, "broadcast", False) else "grupo"
            grupos.append({
                "id": dialog.id,
                "nome": dialog.name,
                "tipo": tipo,
            })
    return grupos


async def selecionar_grupo(client: TelegramClient) -> int | None:
    """Mostra grupos disponíveis e retorna o ID do grupo escolhido.

    Salva a escolha no .env automaticamente. Retorna None se o usuário
    não escolher nenhum grupo.
    """
    grupos = await listar_grupos(client)

    if not grupos:
        console.print("[red]Nenhum grupo encontrado na sua conta.[/red]")
        return None

    table = Table(title="Seus grupos e canais", show_header=True, header_style="bold cyan")
    table.add_column("#", justify="right", style="bold")
    table.add_column("Tipo", style="dim")
    table.add_column("ID")
    table.add_column("Nome", style="bold")

    for i, g in enumerate(grupos, 1):
        cor_tipo = "blue" if g["tipo"] == "grupo" else "magenta"
        table.add_row(str(i), f"[{cor_tipo}]{g['tipo']}[/{cor_tipo}]", str(g["id"]), g["nome"])

    console.print()
    console.print(Panel(table, title="[bold]Telegram[/bold]", border_style="blue"))
    console.print()

    escolha = input("Digite o número do grupo para monitorar (ou Enter para sair): ").strip()

    if escolha and escolha.isdigit():
        idx = int(escolha) - 1
        if 0 <= idx < len(grupos):
            grupo = grupos[idx]
            _salvar_group_id(grupo["id"])
            console.print(f"\n[green]✅ Grupo configurado:[/green] {grupo['nome']} (ID: {grupo['id']})")
            return grupo["id"]
        else:
            console.print("[red]Número inválido.[/red]")
            return None

    return None


def _salvar_group_id(group_id: int):
    """Atualiza TELEGRAM_GROUP_ID no arquivo .env."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

    with open(env_path, "r") as f:
        content = f.read()

    content = re.sub(
        r"TELEGRAM_GROUP_ID=.*",
        f"TELEGRAM_GROUP_ID={group_id}",
        content,
    )

    with open(env_path, "w") as f:
        f.write(content)


if __name__ == "__main__":
    import asyncio

    from dotenv import load_dotenv

    load_dotenv()

    api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash = os.getenv("TELEGRAM_API_HASH", "")

    async def _main():
        client = TelegramClient("helpertips", api_id, api_hash)
        await client.start()
        await selecionar_grupo(client)
        await client.disconnect()

    asyncio.run(_main())
