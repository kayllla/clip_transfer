import subprocess
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich import print as rprint

from clip_gen import generate_clip
from transitions import render_preview, render_final
from agent import design_transitions

console = Console()


def open_preview(path: str):
    subprocess.Popen(["open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def get_prompts() -> tuple[list[str], str]:
    console.print(Panel.fit(
        "[bold cyan]Clip Transfer[/bold cyan]  [dim]AI 视频转场 Demo[/dim]",
        border_style="cyan",
    ))

    style = Prompt.ask("\n[green]整体风格[/green]", default="cinematic, dramatic lighting")
    console.print()

    prompts = []
    console.print("[yellow]输入每段 clip 的 prompt（2-3段，直接回车结束）[/yellow]")
    for i in range(3):
        p = Prompt.ask(f"  [dim]Clip {i+1}[/dim]")
        if not p:
            break
        prompts.append(p)

    if len(prompts) < 2:
        console.print("[red]至少需要 2 段 clip[/red]")
        sys.exit(1)

    return prompts, style


def generate_all_clips(prompts: list[str]) -> list[str]:
    clips = []
    for i, prompt in enumerate(prompts):
        console.print(f"\n  生成 Clip {i+1}/{len(prompts)}...", end=" ")
        path = generate_clip(prompt, clip_index=i + 1)
        console.print(f"[green]✓[/green] [dim]{path}[/dim]")
        clips.append(path)
    return clips


def handle_transition(i: int, clips: list[str], prompts: list[str], style: str) -> dict:
    """Interactive loop for one transition pair. Returns the chosen transition dict."""
    console.rule(f"[bold]转场 {i+1} → {i+2}[/bold]")
    feedback = ""

    while True:
        with console.status("Claude 设计转场方案..."):
            options = design_transitions(prompts[i], prompts[i + 1], style, feedback)

        # Render previews
        previews = []
        for j, opt in enumerate(options):
            with console.status(f"渲染预览 {j+1}/3..."):
                try:
                    path = render_preview(clips[i], clips[i + 1], opt["transition"], opt["duration"])
                    previews.append(path)
                except Exception as e:
                    console.print(f"[red]预览 {j+1} 渲染失败: {e}[/red]")
                    previews.append(None)

        # Show options table
        table = Table(show_header=False, box=None, padding=(0, 2))
        for j, (opt, preview) in enumerate(zip(options, previews)):
            status = "[green]✓[/green]" if preview else "[red]✗[/red]"
            table.add_row(
                f"[bold cyan][{j+1}][/bold cyan]",
                f"[cyan]{opt['transition']}[/cyan] ({opt['duration']}s)",
                opt["why"],
                status,
            )
        console.print(table)

        # Open valid previews
        for preview in previews:
            if preview:
                open_preview(preview)

        console.print("\n[dim]预览已在播放器中打开[/dim]")
        choice = Prompt.ask("选择 [bold][1/2/3][/bold] 或输入修改意见")

        if choice in ("1", "2", "3"):
            chosen = options[int(choice) - 1]
            console.print(f"  → [green]已选择[/green] [cyan]{chosen['transition']}[/cyan]\n")
            return chosen

        # User wants changes — pass feedback back to Claude
        feedback = choice
        console.print()


def main():
    prompts, style = get_prompts()

    console.rule("[bold]生成 Clips[/bold]")
    clips = generate_all_clips(prompts)

    chosen_transitions = []
    for i in range(len(clips) - 1):
        trans = handle_transition(i, clips, prompts, style)
        chosen_transitions.append(trans)

    console.rule("[bold]合并最终视频[/bold]")
    with console.status("FFmpeg 合并中..."):
        out = render_final(clips, chosen_transitions)

    console.print(f"\n[bold green]完成！[/bold green] 输出：[cyan]{out}[/cyan]")
    open_preview(out)


if __name__ == "__main__":
    main()
