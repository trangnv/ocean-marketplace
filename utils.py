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
