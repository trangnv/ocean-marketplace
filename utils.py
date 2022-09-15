import requests
import json
import pandas as pd
from enforce_typing import enforce_types
import json
from typing import Any, Dict, List, Tuple
import csv


def get_block_number_from_timestamp(timestamp):
    url = f"https://api.polygonscan.com/api?module=block&action=getblocknobytime&timestamp={timestamp}&closest=before&apikey=TPM27R128ZBPXS9QEJKWQJ9S6BYTCJ8EB4"
    headers = {"Content-Type": "application/json"}
    responses = requests.request("POST", url, headers=headers)
    data = json.loads(responses.text)
    return int(data["result"])


def submitQuery(query: str, chainID: int) -> dict:
    subgraph_url = chainIdToSubgraphUri(chainID)
    request = requests.post(subgraph_url, "", json={"query": query})
    if request.status_code != 200:
        raise Exception(f"Query failed. Return code is {request.status_code}\n{query}")

    result = request.json()

    return result


class DataNFT:
    def __init__(
        self,
        nft_addr: str,
        chain_id: int,
        _symbol: str,
        name: str,
        basetoken_addr: str,
        volume: float,
    ):
        self.nft_addr = nft_addr
        # self.did = oceanutil.calcDID(nft_addr, chain_id)
        self.chain_id = chain_id
        self.symbol = _symbol
        self.name = name
        self.basetoken_addr = basetoken_addr
        self.volume = volume

    def __repr__(self):
        return f"{self.nft_addr} {self.chain_id} {self.symbol} {self.name}"


# class Datatoken:
#     def __init__(self, datatoken_addr: str, chain_id: int, _symbol: str):
#         self.datatoken_addr = datatoken_addr
#         self.chain_id = chain_id


def getNFTVolumes(
    st_block: int, end_block: int, chainID: int
) -> Tuple[Dict[str, Dict[str, float]], List[DataNFT]]:
    """
    @description
      Query the chain for datanft volumes within the given block range.

    @return
      nft_vols_at_chain -- dict of [basetoken_addr][nft_addr]:vol_amt
      NFTinfo -- list of DataNFT objects
    """
    print("getVolumes(): begin")

    NFTvols: Dict[str, Dict[str, float]] = {}
    NFTinfo_tmp: Dict[str, Dict[str, Dict[str, Any]]] = {}
    NFTinfo = []

    chunk_size = 1000  # max for subgraph = 1000
    offset = 0
    while True:
        query = """
        {
          orders(where: {block_gte:%s, block_lte:%s}, skip:%s, first:%s) {
            id,
            datatoken {
              id
              symbol
              nft {
                id
                name
                symbol
              }
            },
            lastPriceToken,
            lastPriceValue,
            block
          }
        }
        """ % (
            st_block,
            end_block,
            offset,
            chunk_size,
        )
        offset += chunk_size
        result = submitQuery(query, chainID)
        new_orders = result["data"]["orders"]
        if new_orders == []:
            break
        for order in new_orders:
            lastPriceValue = float(order["lastPriceValue"])
            if lastPriceValue == 0:
                continue
            nft_addr = order["datatoken"]["nft"]["id"].lower()
            basetoken_addr = order["lastPriceToken"]

            if basetoken_addr not in NFTvols:
                NFTvols[basetoken_addr] = {}

            if nft_addr not in NFTvols[basetoken_addr]:
                NFTvols[basetoken_addr][nft_addr] = 0.0
            NFTvols[basetoken_addr][nft_addr] += lastPriceValue

            ### Store nft symbol for later use
            if not basetoken_addr in NFTinfo_tmp:
                NFTinfo_tmp[basetoken_addr] = {}

            if not nft_addr in NFTinfo_tmp[basetoken_addr]:
                NFTinfo_tmp[basetoken_addr][nft_addr] = {}

            NFTinfo_tmp[basetoken_addr][nft_addr]["symbol"] = order["datatoken"]["nft"][
                "symbol"
            ]
            NFTinfo_tmp[basetoken_addr][nft_addr]["name"] = order["datatoken"]["nft"][
                "name"
            ]

    for base_addr in NFTinfo_tmp:
        for nft_addr in NFTinfo_tmp[base_addr]:
            datanft = DataNFT(
                nft_addr,
                chainID,
                NFTinfo_tmp[base_addr][nft_addr]["symbol"],
                NFTinfo_tmp[base_addr][nft_addr]["name"],
                base_addr,
                NFTvols[base_addr][nft_addr],
            )
            NFTinfo.append(datanft)

    print("getVolumes(): done")
    return NFTvols, NFTinfo


_CHAINID_TO_NETWORK = {
    8996: "development",  # ganache
    1: "mainnet",
    3: "ropsten",
    4: "rinkeby",
    56: "bsc",
    137: "polygon",
    246: "energyweb",
    1287: "moonbase",
    1285: "moonriver",
    80001: "mumbai",
}


@enforce_types
def chainIdToSubgraphUri(chainID: int) -> str:
    """Returns the subgraph URI for a given chainID"""
    sg = "/subgraphs/name/oceanprotocol/ocean-subgraph"
    # if chainID == DEV_CHAINID:
    #     return "http://127.0.0.1:9000" + sg

    network_str = chainIdToNetwork(chainID)
    return f"https://v4.subgraph.{network_str}.oceanprotocol.com" + sg


@enforce_types
def chainIdToNetwork(chainID: int) -> str:
    """Returns the network name for a given chainID"""
    return _CHAINID_TO_NETWORK[chainID]


@enforce_types
def saveNFTvolsCsv(nftvols_at_chain: dict, csv_file: str, chainID: int):
    """
    @description
      Save the nftvols csv for this chain. This csv is a key input for
      dftool calcrewards, and contains just enough info for it to operate, and no more.

    @arguments
      nftvols_at_chain -- dict of [basetoken_addr][nft_addr] : vol_amt
      csv_dir -- directory that holds csv files
      chainID -- which network
    """
    # assert os.path.exists(csv_dir), csv_dir
    # csv_file = nftvolsCsvFilename(csv_dir, chainID)
    # assert not os.path.exists(csv_file), csv_file
    V = nftvols_at_chain
    with open(csv_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["chain_id", "basetoken_address", "nft_address", "volume_amount"]
        )
        for basetoken_addr in V.keys():
            # assertIsEthAddr(basetoken_addr)
            for nft_addr, vol in V[basetoken_addr].items():
                # assertIsEthAddr(nft_addr)
                row = [chainID, basetoken_addr.lower(), nft_addr.lower(), vol]
                writer.writerow(row)
    print(f"Created {csv_file}")
