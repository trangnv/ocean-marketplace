import requests
import json
import pandas as pd


def get_block_number_from_timestamp(timestamp):
    url = f"https://api.polygonscan.com/api?module=block&action=getblocknobytime&timestamp={timestamp}&closest=before&apikey=TPM27R128ZBPXS9QEJKWQJ9S6BYTCJ8EB4"
    headers = {"Content-Type": "application/json"}
    responses = requests.request("POST", url, headers=headers)
    data = json.loads(responses.text)
    return int(data["result"])


# def get_global_statistics_polygon(from_timestamp, to_timestamp, interval):
#     df_global_statistics = pd.DataFrame(
#         columns=[
#             "totalLiquidity.value",
#             "totalLiquidity.token.address",
#             "datatokenCount",
#             "fixedCount",
#             "nftCount",
#             "poolCount",
#             "block",
#             "timestamp",
#         ]
#     )
#     timestamp0 = 1653868800  # (GMT): Monday, May 30, 2022 12:00:00 AM
#     timestamp1 = 1658534400  # (GMT): Saturday, July 23, 2022 12:00:00 AM

#     base_url = "https://v4.subgraph.polygon.oceanprotocol.com"
#     route = "/subgraphs/name/oceanprotocol/ocean-subgraph"
#     url = base_url + route


# for timestamp in range(timestamp0, timestamp1, 21600):  # 21600 / 3600 = 6 hours
#     block_number = get_block_number_from_timestamp(timestamp)
#     query = f"""
#     {{
#       globalStatistics (
#         block: {{
#           number: {block_number}
#         }}
#       )
#       {{
#         nftCount
#         datatokenCount
#         totalLiquidity {{
#           value
#           token {{
#             address
#           }}
#         }}
#         poolCount
#         fixedCount
#       }}
#     }}
#   """
#     headers = {"Content-Type": "application/json"}
#     payload = json.dumps({"query": query})
#     response = requests.request("POST", url, headers=headers, data=payload)
#     data = json.loads(response.text)

#     df_data = pd.json_normalize(
#         data["data"]["globalStatistics"],
#         record_path=["totalLiquidity"],
#         meta=["datatokenCount", "fixedCount", "nftCount", "poolCount"],
#     )
#     df_data.rename(
#         {
#             "value": "totalLiquidity.value",
#             "token.address": "totalLiquidity.token.address",
#         },
#         axis=1,
#         inplace=True,
#     )

#     df_data["block"] = block_number
#     df_data["timestamp"] = timestamp
#     time.sleep(0.25)

#     df_global_statistics = pd.concat(
#         [df_global_statistics, df_data], ignore_index=True, sort=False
#     )

import json
from typing import Any, Dict, List, Tuple
import networkutil


def submitQuery(query: str, chainID: int) -> dict:
    subgraph_url = networkutil.chainIdToSubgraphUri(chainID)
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
        basetoken_addr: str,
        volume: float,
    ):
        self.nft_addr = nft_addr
        # self.did = oceanutil.calcDID(nft_addr, chain_id)
        self.chain_id = chain_id
        self.symbol = _symbol
        self.basetoken_addr = basetoken_addr
        self.volume = volume

    def __repr__(self):
        return f"{self.nft_addr} {self.chain_id} {self.symbol}"# {self.symbol}"


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

            NFTinfo_tmp[basetoken_addr][nft_addr]["symbol"] = order["datatoken"][
                "symbol"
            ]

    for base_addr in NFTinfo_tmp:
        for nft_addr in NFTinfo_tmp[base_addr]:
            datanft = DataNFT(
                nft_addr,
                chainID,
                NFTinfo_tmp[base_addr][nft_addr]["symbol"],
                base_addr,
                NFTvols[base_addr][nft_addr],
            )
            NFTinfo.append(datanft)

    print("getVolumes(): done")
    return NFTvols, NFTinfo
