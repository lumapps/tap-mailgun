# tap-mailgun

`tap-mailgun` is a Singer tap for Mailgun.

Built with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.

## Installation

Install from PyPI:

```bash
pipx install tap-mailgun
```

Install from GitHub:

```bash
pipx install git+https://github.com/ORG_NAME/tap-mailgun.git@main
```

## Configuration

### Accepted Config Options

A full list of supported settings and capabilities for this
tap is available by running:

```bash
tap-mailgun --about
```

### Configure using environment variables

This Singer tap will automatically import any environment variables within the working directory's
`.env` if the `--config=ENV` is provided, such that config values will be considered if a matching
environment variable is set either in the terminal context or in the `.env` file.

### Source Authentication and Authorization

The Mailgun API uses API keys for authentication. You will need to provide your Mailgun API key in the configuration.

## Usage

You can easily run `tap-mailgun` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Tap Directly

```bash
tap-mailgun --version
tap-mailgun --help
tap-mailgun --config CONFIG --discover > ./catalog.json
```

## Supported Streams

This tap supports the following streams:

* [`analytics_metrics`](https://documentation.mailgun.com/en/latest/api-stats.html#stats): Retrieves aggregate statistics for events such as `accepted`, `delivered`, `failed`, `opened`, `clicked`, `unsubscribed`, `complained`, or `stored`.

## Developer Resources

Follow these instructions to contribute to this project.

### Initialize your Development Environment

Prerequisites:

* Python 3.9+
* [uv](https://docs.astral.sh/uv/)

```bash
uv sync
```

### Create and Run Tests

Create tests within the `tests` subfolder and
then run:

```bash
uv run pytest
```

You can also test the `tap-mailgun` CLI interface directly using `uv run`:

```bash
uv run tap-mailgun --help
```

### Testing with [Meltano](https://www.meltano.com)

_**Note:** This tap will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install meltano
pipx install meltano
# Initialize meltano within this directory
cd tap-mailgun
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke tap-mailgun --version

# OR run a test ELT pipeline:
meltano run tap-mailgun target-jsonl
```
