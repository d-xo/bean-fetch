# bean-fetch

`bean-fetch` is a tool that fetches raw transaction data from various financial institutions and
transforms it into a single consistent beancount ledger (including prices / cost basis when
required).

`bean-fetch` is currently in development, and is not yet in a usable state.

## Usage

1. Create a `config.yaml` file
1. Run `bean-fetch -c <path_to_config>`

## Configuration

`bean-fetch` is configured by a `yaml` file with the following structure:

```yaml
archive_dir:      # path to the directory where the raw transaction data will be persisted

coinbase:
  api_key:        # coinbase api key (string)
  api_secret:     # coinbase api secret (string)

coinbasepro:
  api_key:        # coinbase pro api key (string)
  api_secret:     # coinbase pro api secret (string)
  api_passphrase: # coinbase pro api passphrase (string)

ethereum:
  rpc_url:        # url of a web3 rpc endpoint (string)
```

## Developing

You can enter a development environment by running `nix-shell` from the project root.

You can then run `bean-fetch` by running:

```
python -m bean_fetch.main -c ~/archive/beancount/config.yml
```

## Architecture

`bean-fetch` has two core functions:

1. Fetch raw data from configured backends and persist it in generic, machine readable format
2. Parse the fetched data and use it to construct a `beancount` ledger

The core data structure in `bean-fetch` is the `RawTx`. This is essentially a json blob with some
metadata attached. This is the format in which data is persisted in the archive.

`bean-fetch` can fetch and process data from many locations. The logic related to each one of these
locations is contained in a strcture called a `Venue`. A `Venue` must implement in the `VenueLike`
interface defined in `data.py`. This consists of three methods:

### `fetch(config: Config) -> List[RawTx[Kind]]`

`fetch` takes a `Config` object and returns a list of `RawTx`. Both the `Config` and `Kind` objects
are defined within the venue themselves.

### `handles(tx: RawTx[Kind]) -> bool`

`handles` takes a `RawTx` and returns true if it is able to be parsed by this `Venue`.

### `parse(config: Config, tx: RawTx[Kind]) -> Transaction`

`parse` takes a `Config` and a `RawTx` and returns a beancount `Transaction` object.
