#! /usr/bin/env bash

set -euo pipefail

# clean up
trap 'killall geth && rm -rf "$TMPDIR"' EXIT
trap "exit 1" SIGINT SIGTERM

TMPDIR=$(mktemp -d)
dapp testnet --dir "$TMPDIR" &
sleep 10

export ETH_RPC_URL="http://127.0.0.1:8545"
export ETH_GAS=9999999999
export ETH_RPC_ACCOUNTS=1

read -r ACC _ <<< "$(seth ls --keystore "$TMPDIR/.dapp/testnet/8545/keystore")"
export ETH_FROM=$ACC

function sendEth() {
    local to=$1
    local value=$2
    seth send --value "$(seth --to-wei "$value" eth)" "$to"
}

function deployUniswapFactory() {
    local jsonFile
    local bytecode
    local url=https://unpkg.com/@uniswap/v2-core@1.0.1/build/UniswapV2Factory.json

    jsonFile=$(mktemp)
    curl -s "$url" > "$jsonFile"
    bytecode=$(jq -r .bytecode < "$jsonFile")

    seth send --create "$bytecode" "constructor(address)" "$ETH_FROM"
}

function deployWeth() {
    local sourceUrl=https://raw.githubusercontent.com/dapphub/ds-weth/master/src/weth9.sol
    local bytecode
    local source

    source=$(mktemp)
    curl -s "$sourceUrl" > "$source"
    bytecode=$(seth --nix-run solc-versions.solc_0_4_23 solc --bin "$source")
    bytecode=$(echo "$bytecode" | awk 'f{print;f=0} /Binary:/{f=1}')

    seth send --create "$bytecode"
}

function deployRouter() {
    local factory=$1
    local weth=$2

    local jsonFile
    local bytecode
    local url=https://unpkg.com/@uniswap/v2-periphery@1.1.0-beta.0/build/UniswapV2Router02.json

    jsonFile=$(mktemp)
    curl -s "$url" > "$jsonFile"
    bytecode=$(jq -r .bytecode < "$jsonFile")

    seth send --create "$bytecode" "constructor(address,address)" "$factory" "$weth"
}

function deployToken() {
    local sourceUrl=https://raw.githubusercontent.com/xwvvvvwx/weird-erc20/main/src/ERC20.sol
    local bytecode
    local source

    source=$(mktemp)
    curl -s "$sourceUrl" > "$source"
    bytecode=$(seth --nix-run solc-versions.solc_0_6_12 solc --bin "$source")
    bytecode=$(echo "$bytecode" | awk 'f{print;f=0} /Binary:/{f=1}')

    seth send --create "$bytecode" "constructor(uint256)" "$(seth --to-wei 999999999 eth)"
}

function msg() {
    echo
    echo ---------------------------------------------------------------------
    echo "$@"
    echo ---------------------------------------------------------------------
    echo
}

msg sending some eth

msg deploying uniswap factory
factory=$(deployUniswapFactory)
msg deploying ERC20 tokens
token0=$(deployToken)
token1=$(deployToken)
msg deploying WETH
weth=$(deployWeth)
msg deploying router
router=$(deployRouter "$factory" "$weth")

msg "creating uniswap pair for $token0 and $token1"
seth send "$factory" "createPair(address,address)" "$token0" "$token1"
pair=$(seth call "$factory" "getPair(address,address)(address)" "$token0" "$token1")

msg approving the router against both tokens
seth send "$token0" "approve(address,uint256)" "$router" "$(seth --to-int256 -1)"
seth send "$token1" "approve(address,uint256)" "$router" "$(seth --to-int256 -1)"

msg approving the router against pair
seth send "$pair" "approve(address,uint256)" "$router" "$(seth --to-int256 -1)"

msg adding some liquidity
seth send "$router" "addLiquidity(address,address,uint,uint,uint,uint,address,uint)" "$token0" "$token1" "$(seth --to-wei 1000 eth)" "$(seth --to-wei 100 eth)" 0 0 "$ETH_FROM" "$(seth --to-int256 -1)"

msg swapping some tokens
seth send "$router" "swapExactTokensForTokens(uint,uint,address[],address,uint)" "$(seth --to-wei 10 eth)" 0 "[$token0, $token1]" "$ETH_FROM" "$(seth --to-int256 -1)"
seth send "$router" "swapExactTokensForTokens(uint,uint,address[],address,uint)" "$(seth --to-wei 60 eth)" 0 "[$token1, $token0]" "$ETH_FROM" "$(seth --to-int256 -1)"

msg removing some liquidity
shares=$(seth call "$pair" "balanceOf(address)(uint)" "$ETH_FROM")
seth send "$router" "removeLiquidity(address,address,uint,uint,uint,address,uint)" "$token0" "$token1" "$shares" 0 0 "$ETH_FROM" "$(seth --to-int256 -1)"

msg running bean-fetch
beanDir=$(mktemp -d)
cat > "$beanDir/config.yml" <<EOL
archive_dir: ./archive

ethereum:
  rpc_url: http://127.0.0.1:8545
  start_block: 0
  addresses:
    - "$(seth --to-address "$ETH_FROM")" # testnet
EOL
python -m bean_fetch.main -c "$beanDir/config.yml"

msg raw transactions written to "$beanDir/archive"
