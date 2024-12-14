import aiohttp
import asyncio
import zlib
import time
from google.protobuf import json_format
import response_pb2  # This is the compiled Protobuf file
import re
import os
import sys

# Replace these with your actual values
app_id = "com.amadeus.merci.client.ui"
auth_token = os.getenv("AUTH_TOKEN")
output_dir = os.path.join("apps", app_id)
os.makedirs(output_dir, exist_ok=True)

# Ensure token is present
if not auth_token:
    print("Error: AUTH_TOKEN environment variable is missing.")
    sys.exit(1)

# Retry configuration
max_retries = 1000
retry_delay = 2  # Seconds between retries

headers = {
    'accept-encoding': 'br',
    'accept-language': 'en-AU',
    'authorization': f'Bearer {auth_token}',
    'connection': 'keep-alive',
    'host': 'play-fe.googleapis.com',
    'user-agent': 'Android-Finsky/43.2.16-29 [0] [PR] 686207179 (api=3,versionCode=84321620,sdk=30,device=a71,hardware=qcom,product=a71nsxx,platformVersionRelease=11,model=SM-A715F,buildId=RP1A.200720.012,isWideScreen=0,supportedAbis=arm64-v8a;armeabi-v7a)',
    'x-dfe-userlanguages': 'en_AU',
    'x-ps-rh': 'H4sIAAAAAAAAAF2RzavjZBTGJ3dm8FIXDhcEGUREHBiE3JukTZsObk6-mrfNm-ajaZq7Kflq2iZt7k3aJulqGP-BWYpLvxaC_4A7cefClSvdCYJLZRBhxoWZmbvyhcN54IHnnN95W58QrceE0ikQ3Lw5i2u2QgyeuEftiGlNxJWWGxQ-um08sSl5qsbSGiitN6KwCHThCxSG6WgD2yoYHDnSyZQNJwzE-XiLzcMw0OU6mGn4oCM0UtSYvUIccowxKMMEtHT2cqb57Hbrz9utxycCYGtfSlpW-jqrZpoHM-laxwM-Z3h-6AC_63WZsnaEQ6Vk0PZEbTgFLabKpb5WRkiGUbKEIZcBRladzCZSFoxAbQpxA9BKCbRsnfX0jWQIjqglC8BYAI0e82Oq8RHilY5UgQsMjIE3hBAMAXjgIxi6ehsk4OIO7MGGBRg6j7FNxj4GJEkwRlJRmooVZQPQMxHGpQ4DBGyMdqBxchbbEJeUlJa6zvP2dH_J1EInX7LxcbYlDXNptTl5L03O_iBenuDakLQoP2x28T6EQFlDJxlwrBqImoL4WHBIw-NsEMWRAQ1eGafNWkyNpN3q4Da-KnZIil0OfOXKlAC5DZo7SMAArkHIDAeL49JkYluqG9SjGUAOCLaAxdQY13yQyQ3usKz8uEGUPMCBvhQTocxg3mRUpQtJ7GlQijsYSr5skfNCdVWmVpw8MjC18q1t7Ni7sWsehK6t7bgBa_jpyCFD8ZqLGD5fCaG7vX_r8mui9QUhgeSCgARjOhXkOBuYFNqZNqtIcYmY8Hqwj12jxIJFG8ORFGdC41sirC-ZzOvyS6GTXulTSIeCsLQrLNqldnTZplf4KFV4gjt4jY6NNsDMVAFvnZ4fDyRtNZ8LSS3Cyoi7m6LJgZxb5DDJlICRd0G7-SEKicGarxwA_-T0bn7rCfGcaP1DAC9LO9rOc2OmbY5WkrdNHO7Wkc2kG8GqrHgKx3GtLC7ryjb71KwdHSwdhg59mZB-tLOcpdot2cttlwwMqijkw7Q3982EBamnLnvaeB8Wxp4-bJBaF8ieUduI3DAhwmlqdhkrmLDasHQN3g2naumM08m0ZGpmXIDcGWncnrW4arFS5urQqVQvTYFDqZUkhXzl68Ky7k-1fcRVvclsMdtd-YJc1pbUzTuJtDsqMKPIRJlMFm3Ps3Vtj9D1kS7dYQBt1v6c6LXePX3v7C1Tp-GcoageQ51TNHP_hKbf__nHzx6eve1tSG8b5tkqJAtvU-y3MVkU7xDfEF8Srdtejz67cx1km_unFiahR7PyB4y82hZJfdFpnzPndJdk-g8Y6gHLNyW-Vrr5Wna5LkP16F7_ozeaoG1RVdSzFy---_vx9z99_Ei-mXZxY73sj2j64n-bXrwaOpvZHD8F5tG-iPKLPEojr4jIJKqLX4iHrQ_7YRi2Oc4n6dCPyA7d90g_ZDtkxHj9fqfPLLg-d-_kN-LO6bd_3X1OvHnv039_ffLD06-e_k78Byz2kNtLBQAA'
}

# Helper function to check if data is likely Protobuf format
def is_probably_protobuf(input_bytes):
    if len(input_bytes) < 2:
        return False
    field_number_trunc = input_bytes[0] >> 3
    field_type = input_bytes[0] & 0b111
    return 1 <= field_number_trunc <= 3 and field_type in {0, 1, 2, 5}

# Decompress message based on encoding, if applicable
def decompress_if_needed(data, encoding):
    if encoding == 'gzip':
        return zlib.decompress(data, zlib.MAX_WBITS | 16)
    elif encoding == 'deflate':
        return zlib.decompress(data, -zlib.MAX_WBITS)
    return data

# Parse Protobuf message to a dictionary
def parse_protobuf_message(message_data):
    try:
        protobuf_msg = response_pb2.Response()
        protobuf_msg.ParseFromString(message_data)
        return json_format.MessageToJson(protobuf_msg)  # Convert to JSON for easier inspection
    except Exception as e:
        print("Failed to decode Protobuf message:", e)
        return None
    
# Helper function to check if the token is valid by testing a known version
async def test_auth_token(session):
    url = f"https://play-fe.googleapis.com/fdfe/delivery?doc={app_id}&ot=1&vc=1"
    async with session.get(url) as response:
        if response.status == 200:
            response_data = await response.read()
            
            # Check if the response contains an HTTP/HTTPS URL, indicating a valid response
            if re.search(rb'https?://', response_data):
                print("Auth token is valid.")
                return True
            else:
                print("Auth token might be expired or invalid - no URL found in response.")
                return False

# Async function to handle each request with retry logic
async def fetch_and_save(session, url, vc, semaphore):
    async with semaphore:  # Control concurrency
        retries = 0
        while retries <= max_retries:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        # Check for Content-Encoding to handle decompression
                        encoding = response.headers.get('Content-Encoding', None)
                        response_data = decompress_if_needed(await response.read(), encoding)

                        # Check for HTTP/HTTPS URL in raw data
                        if re.search(rb'https?://', response_data):
                            print(f"Version code {vc} response contains URL, saving...")

                            # Save raw response data to a binary file within apps/app_id folder
                            filename = os.path.join(output_dir, f"{vc}.bin")
                            with open(filename, "wb") as file:
                                file.write(response_data)

                            # Parse and print the Protobuf message as JSON
                            parsed_json = parse_protobuf_message(response_data)
                            if parsed_json:
                                print(f"Parsed response for version code {vc}:", parsed_json)
                            else:
                                print(f"Failed to parse Protobuf message for version code {vc}.")
                        else:
                            print(f"Version code {vc} response does not contain an HTTP/HTTPS URL, not saving.")
                        return  # Exit the function if request is successful

                    elif 500 <= response.status < 600:
                        # Retry for 50x errors
                        retries += 1
                        print(f"Request failed with status {response.status} for version code {vc}, retrying {retries}/{max_retries}...")
                        await asyncio.sleep(retry_delay)
                    else:
                        # Handle non-50x errors (do not retry)
                        print(f"Request failed for version code {vc} with status {response.status}, not retrying.")
                        return

            except aiohttp.ClientOSError as e:
                # Retry on ClientOSError
                retries += 1
                print(f"ClientOSError for version code {vc}, retrying {retries}/{max_retries}...: {e}")
                await asyncio.sleep(retry_delay)

        # If we exhaust all retries
        print(f"Max retries exceeded for version code {vc}, skipping.")

# Main async function
async def main():
    version_code_start = 1212500000
    version_code_end = 1213000000
    max_concurrent_requests = 100
    semaphore = asyncio.Semaphore(max_concurrent_requests)

    # Timeout for the ClientSession to handle long response times
    timeout = aiohttp.ClientTimeout(total=30)  # 30 seconds

    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        if not await test_auth_token(session):
            print("Error: The auth token might have expired. Exiting.")
            return
        tasks = []
        for vc in range(version_code_start, version_code_end + 1):
            url = f"https://play-fe.googleapis.com/fdfe/delivery?doc={app_id}&ot=1&vc={vc}"
            tasks.append(fetch_and_save(session, url, vc, semaphore))
        await asyncio.gather(*tasks)

# Run the async main function
asyncio.run(main())
