import urllib.request
import urllib.parse
import json

def test_api():
    api_key = "6ce6d8855b500ea8797d4bb6e1bb1fa4"

    # Test with valid coordinates (Moscow)
    lat = 55.7558
    lon = 37.6173

    # Build URL with parameters
    url = "https://api.openweathermap.org/data/2.5/uvi"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key
    }

    # Encode parameters
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"

    print(f"Making request to: {full_url}")

    try:
        response = urllib.request.urlopen(full_url)
        response_text = response.read().decode('utf-8')

        print(f"Response status: {response.getcode()}")
        print(f"Response text: {response_text}")

        if response.getcode() == 200:
            data = json.loads(response_text)
            print(f"Parsed JSON data: {data}")
            print("API call successful!")
        else:
            print("Error occurred - this might be the same error you're seeing")

    except urllib.error.HTTPError as e:
        error_text = e.read().decode('utf-8')
        print(f"HTTP Error {e.code}: {error_text}")
    except Exception as e:
        print(f"Exception occurred: {e}")

# Run the test
test_api()