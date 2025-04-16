from bs4 import BeautifulSoup
import subprocess, urllib.parse, time, json

#目的地を指定
goalStation = "松ヶ崎（京都府）"
#到着時刻を指定
year, month, day, hour, minute = '2025', '04', '16', '8', '43'
#調査対象の都道府県を指定
prefList = ['08', '11', '12', '13', '14', '17', '18', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '33', '34', '35', '37', '38']

def getSoup(url):
    result = subprocess.run(
        ["curl", url, "-H", "user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"],
        capture_output=True,
        text=True
    )
    html = result.stdout
    soup = BeautifulSoup(html, "html.parser")
    time.sleep(5)
    return soup


#駅を取得

lines = {}

for pref in prefList:
    url = f"https://www.navitime.co.jp/railroad/raillist?aCode={pref}"
    links = getSoup(url).select("#railroad-list a")

    for link in links:
        lineName = urllib.parse.unquote(link["href"].split("/")[-1])

        if lineName not in lines:
            print(lineName)
            lines[lineName] = []

            stations = getSoup("https://www.navitime.co.jp/" + link["href"]).select(".stop_station_list > dd")

            for station in stations:
                lng = station.get('data-lon')
                lat = station.get('data-lat')
                name = station.select_one(".node_name a").get_text().strip()
                id = station.select_one(".node_name a").get("href").split("=")[1]

                lines[lineName].append([name, id, lng, lat])

    with open("stations.json", "w", encoding="utf-8") as f:
        json.dump(lines, f, ensure_ascii=False, indent=2)


#乗り換え検索

def getData(soup):
    try:
        route = soup.select_one(".summay_route")
        clock = route.select_one("dt").get_text().replace('\xa0', '').split("⇒")
        departure, arrival = clock[0], clock[1]
        required = soup.select_one(".required_time .text").get_text().strip()
        
        fee = route.select_one(".cash").get_text().replace("円", "")
        count = route.select_one(".required_transfer .text").get_text().replace("乗換", "").replace("回", "").strip()

        iconList = []
        icons = route.select(".icon_list img")
        for icon in icons:
            text = icon.get("src").split("/")[-1].split(".png")[0].replace("transfer_r_icon_", "").replace("_01", "")
            iconList.append(text)

        return [departure, arrival, required, fee, count, iconList]
    except Exception as e:
        print(e)
        return []
    

output = {}
goalStationQuote = urllib.parse.quote(goalStation)

for line in lines:
    for station in lines[line]:
        if station[1] not in output:
            url1 = f"https://www.navitime.co.jp/transfer/searchlist?orvStationName=&dnvStationName={goalStationQuote}&thrStationName1=&thrStationCode1=&thrStationName2=&thrStationCode2=&thrStationName3=&thrStationCode3=&month={year}%2F{month}&day={day}&hour={hour}&minute={minute}&orvStationCode={station[1]}&dnvStationCode=&basis=0&from=view.transfer.searchlist&freePass=0&sort=4&wspeed=66&mtrplbus=1&accidentRailCode=&accidentRailName=&isrec="
            url2 = f"https://www.navitime.co.jp/transfer/searchlist?orvStationName=&dnvStationName={goalStationQuote}&thrStationName1=&thrStationCode1=&thrStationName2=&thrStationCode2=&thrStationName3=&thrStationCode3=&month={year}%2F{month}&day={day}&hour={hour}&minute={minute}&orvStationCode={station[1]}&dnvStationCode=&basis=0&from=view.transfer.searchlist&freePass=0&sort=4&wspeed=66&airplane=1&sprexprs=1&utrexprs=1&othexprs=1&mtrplbus=1&accidentRailCode=&accidentRailName=&isrec="
            data = {
                "name": station[0],
                "normal": getData(getSoup(url1)),
                "billing": getData(getSoup(url2)),
                "lng": station[2],
                "lat": station[3]
            }
            print(station[0], data)
            output[station[1]] = data

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)