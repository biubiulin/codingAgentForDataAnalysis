import argparse
from demos import coding_agent_demo_cli, coding_agent_demo_ui


def main():
    parser = argparse.ArgumentParser(description="Coding Agent for Data Analysis")
    parser.add_argument(
        "--mode",
        choices=["cli", "ui"],
        default="ui",
        help="Run in CLI mode or launch Gradio UI",
    )
    args = parser.parse_args()

    if args.mode == "cli":
        coding_agent_demo_cli()
    else:
        coding_agent_demo_ui()


if __name__ == "__main__":
    main()
