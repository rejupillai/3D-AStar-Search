"""336 Major US Cities across all 50 states with Albers USA SVG projection."""

from __future__ import annotations
import math
from typing import Any

# Raw list of 336 major US cities across all 50 states: (Name, State, Latitude, Longitude)
RAW_CITIES: list[tuple[str, str, float, float]] = [
    # Alabama (7)
    ("Birmingham", "AL", 33.5186, -86.8104),
    ("Montgomery", "AL", 32.3792, -86.3077),
    ("Mobile", "AL", 30.6954, -88.0399),
    ("Huntsville", "AL", 34.7304, -86.5861),
    ("Tuscaloosa", "AL", 33.2098, -87.5692),
    ("Dothan", "AL", 31.2232, -85.3905),
    ("Auburn", "AL", 32.6099, -85.4808),
    # Alaska (4)
    ("Anchorage", "AK", 61.2181, -149.9003),
    ("Fairbanks", "AK", 64.8378, -147.7164),
    ("Juneau", "AK", 58.3019, -134.4197),
    ("Sitka", "AK", 57.0531, -135.3300),
    # Arizona (7)
    ("Phoenix", "AZ", 33.4484, -112.0740),
    ("Tucson", "AZ", 32.2226, -110.9747),
    ("Mesa", "AZ", 33.4152, -111.8315),
    ("Flagstaff", "AZ", 35.1983, -111.6513),
    ("Yuma", "AZ", 32.6927, -114.6277),
    ("Prescott", "AZ", 34.5400, -112.4685),
    ("Kingman", "AZ", 35.1894, -114.0530),
    # Arkansas (6)
    ("Little Rock", "AR", 34.7465, -92.2896),
    ("Fayetteville", "AR", 36.0822, -94.1719),
    ("Fort Smith", "AR", 35.3859, -94.3985),
    ("Jonesboro", "AR", 35.8423, -90.7043),
    ("Pine Bluff", "AR", 34.2284, -92.0032),
    ("Texarkana", "AR", 33.4418, -94.0377),
    # California (16)
    ("Los Angeles", "CA", 34.0522, -118.2437),
    ("San Diego", "CA", 32.7157, -117.1611),
    ("San Jose", "CA", 37.3382, -121.8863),
    ("San Francisco", "CA", 37.7749, -122.4194),
    ("Fresno", "CA", 36.7378, -119.7871),
    ("Sacramento", "CA", 38.5816, -121.4944),
    ("Oakland", "CA", 37.8044, -122.2712),
    ("Bakersfield", "CA", 35.3733, -119.0187),
    ("Riverside", "CA", 33.9806, -117.3755),
    ("Stockton", "CA", 37.9577, -121.2908),
    ("San Bernardino", "CA", 34.1083, -117.2898),
    ("Redding", "CA", 40.5865, -122.3917),
    ("Eureka", "CA", 40.8021, -124.1637),
    ("Santa Barbara", "CA", 34.4208, -119.6982),
    ("San Luis Obispo", "CA", 35.2828, -120.6596),
    ("Barstow", "CA", 34.8958, -117.0228),
    # Colorado (7)
    ("Denver", "CO", 39.7392, -104.9903),
    ("Colorado Springs", "CO", 38.8339, -104.8214),
    ("Fort Collins", "CO", 40.5853, -105.0844),
    ("Pueblo", "CO", 38.2544, -104.6091),
    ("Grand Junction", "CO", 39.0639, -108.5506),
    ("Boulder", "CO", 40.0150, -105.2705),
    ("Durango", "CO", 37.2753, -107.8801),
    # Connecticut (5)
    ("Bridgeport", "CT", 41.1792, -73.1894),
    ("New Haven", "CT", 41.3083, -72.9279),
    ("Hartford", "CT", 41.7658, -72.6734),
    ("Stamford", "CT", 41.0534, -73.5387),
    ("New London", "CT", 41.3557, -72.0995),
    # Delaware (3)
    ("Wilmington", "DE", 39.7447, -75.5484),
    ("Dover", "DE", 39.1582, -75.5244),
    ("Rehoboth Beach", "DE", 38.7198, -75.0760),
    # Florida (11)
    ("Jacksonville", "FL", 30.3322, -81.6557),
    ("Miami", "FL", 25.7617, -80.1918),
    ("Tampa", "FL", 27.9506, -82.4572),
    ("Orlando", "FL", 28.5383, -81.3792),
    ("Tallahassee", "FL", 30.4383, -84.2807),
    ("Fort Lauderdale", "FL", 26.1224, -80.1373),
    ("Fort Myers", "FL", 26.6406, -81.8723),
    ("Pensacola", "FL", 30.4213, -87.2169),
    ("Gainesville", "FL", 29.6516, -82.3248),
    ("Key West", "FL", 24.5551, -81.7800),
    ("Panama City", "FL", 30.1588, -85.6602),
    # Georgia (8)
    ("Atlanta", "GA", 33.7490, -84.3880),
    ("Augusta", "GA", 33.4735, -82.0105),
    ("Columbus", "GA", 32.4610, -84.9877),
    ("Savannah", "GA", 32.0809, -81.0912),
    ("Macon", "GA", 32.8407, -83.6324),
    ("Athens", "GA", 33.9519, -83.3576),
    ("Valdosta", "GA", 30.8327, -83.2785),
    ("Albany", "GA", 31.5785, -84.1557),
    # Hawaii (4)
    ("Honolulu", "HI", 21.3069, -157.8583),
    ("Hilo", "HI", 19.7071, -155.0885),
    ("Kahului", "HI", 20.8893, -156.4729),
    ("Lihue", "HI", 21.9811, -159.3711),
    # Idaho (6)
    ("Boise", "ID", 43.6150, -116.2023),
    ("Idaho Falls", "ID", 43.4917, -112.0339),
    ("Pocatello", "ID", 42.8621, -112.4506),
    ("Twin Falls", "ID", 42.5558, -114.4701),
    ("Coeur d'Alene", "ID", 47.6777, -116.7805),
    ("Lewiston", "ID", 46.4004, -117.0012),
    # Illinois (8)
    ("Chicago", "IL", 41.8781, -87.6298),
    ("Rockford", "IL", 42.2711, -89.0940),
    ("Peoria", "IL", 40.6936, -89.5890),
    ("Springfield", "IL", 39.7817, -89.6501),
    ("Champaign", "IL", 40.1164, -88.2434),
    ("Bloomington", "IL", 40.4842, -88.9937),
    ("Carbondale", "IL", 37.7273, -89.2168),
    ("Quincy", "IL", 39.9356, -91.4099),
    # Indiana (7)
    ("Indianapolis", "IN", 39.7684, -86.1581),
    ("Fort Wayne", "IN", 41.0793, -85.1394),
    ("Evansville", "IN", 37.9716, -87.5711),
    ("South Bend", "IN", 41.6764, -86.2520),
    ("Bloomington", "IN", 39.1653, -86.5264),
    ("Terre Haute", "IN", 39.4667, -87.4139),
    ("Lafayette", "IN", 40.4167, -86.8753),
    # Iowa (7)
    ("Des Moines", "IA", 41.5868, -93.6250),
    ("Cedar Rapids", "IA", 41.9779, -91.6656),
    ("Davenport", "IA", 41.5236, -90.5776),
    ("Sioux City", "IA", 42.4963, -96.4049),
    ("Waterloo", "IA", 42.4928, -92.3426),
    ("Dubuque", "IA", 42.5006, -90.6646),
    ("Council Bluffs", "IA", 41.2619, -95.8608),
    # Kansas (7)
    ("Wichita", "KS", 37.6872, -97.3301),
    ("Topeka", "KS", 39.0473, -95.6752),
    ("Salina", "KS", 38.8403, -97.6114),
    ("Dodge City", "KS", 37.7528, -100.0171),
    ("Hays", "KS", 38.8792, -99.3268),
    ("Manhattan", "KS", 39.1836, -96.5717),
    ("Garden City", "KS", 37.9717, -100.8727),
    # Kentucky (6)
    ("Louisville", "KY", 38.2527, -85.7585),
    ("Lexington", "KY", 38.0406, -84.5037),
    ("Bowling Green", "KY", 36.9685, -86.4808),
    ("Owensboro", "KY", 37.7719, -87.1112),
    ("Paducah", "KY", 37.0834, -88.6000),
    ("Pikeville", "KY", 37.4793, -82.5188),
    # Louisiana (7)
    ("New Orleans", "LA", 29.9511, -90.0715),
    ("Baton Rouge", "LA", 30.4515, -91.1871),
    ("Shreveport", "LA", 32.5252, -93.7502),
    ("Lafayette", "LA", 30.2241, -92.0198),
    ("Lake Charles", "LA", 30.2266, -93.2174),
    ("Monroe", "LA", 32.5093, -92.1193),
    ("Alexandria", "LA", 31.3113, -92.4451),
    # Maine (5)
    ("Portland", "ME", 43.6591, -70.2568),
    ("Bangor", "ME", 44.8016, -68.7712),
    ("Augusta", "ME", 44.3106, -69.7795),
    ("Presque Isle", "ME", 46.6812, -68.0159),
    ("Bar Harbor", "ME", 44.3876, -68.2039),
    # Maryland (5)
    ("Baltimore", "MD", 39.2904, -76.6122),
    ("Frederick", "MD", 39.4143, -77.4105),
    ("Annapolis", "MD", 38.9784, -76.4922),
    ("Salisbury", "MD", 38.3607, -75.5994),
    ("Hagerstown", "MD", 39.6418, -77.7200),
    # Massachusetts (6)
    ("Boston", "MA", 42.3601, -71.0589),
    ("Worcester", "MA", 42.2626, -71.8023),
    ("Springfield", "MA", 42.1015, -72.5898),
    ("Lowell", "MA", 42.6334, -71.3162),
    ("New Bedford", "MA", 41.6362, -70.9342),
    ("Pittsfield", "MA", 42.4501, -73.2454),
    # Michigan (8)
    ("Detroit", "MI", 42.3314, -83.0458),
    ("Grand Rapids", "MI", 42.9634, -85.6681),
    ("Lansing", "MI", 42.7325, -84.5555),
    ("Ann Arbor", "MI", 42.2808, -83.7430),
    ("Flint", "MI", 43.0125, -83.6875),
    ("Kalamazoo", "MI", 42.2917, -85.5872),
    ("Traverse City", "MI", 44.7631, -85.6206),
    ("Marquette", "MI", 46.5436, -87.3954),
    # Minnesota (7)
    ("Minneapolis", "MN", 44.9778, -93.2650),
    ("Saint Paul", "MN", 44.9537, -93.0900),
    ("Rochester", "MN", 44.0121, -92.4802),
    ("Duluth", "MN", 46.7867, -92.1005),
    ("St. Cloud", "MN", 45.5579, -94.1632),
    ("Mankato", "MN", 44.1636, -94.0006),
    ("Bemidji", "MN", 47.4736, -94.8803),
    # Mississippi (6)
    ("Jackson", "MS", 32.2988, -90.1848),
    ("Gulfport", "MS", 30.3674, -89.0928),
    ("Hattiesburg", "MS", 31.3271, -89.2903),
    ("Tupelo", "MS", 34.2576, -88.7034),
    ("Meridian", "MS", 32.3643, -88.7037),
    ("Greenville", "MS", 33.4101, -91.0618),
    # Missouri (7)
    ("Kansas City", "MO", 39.0997, -94.5786),
    ("St. Louis", "MO", 38.6270, -90.1994),
    ("Springfield", "MO", 37.2090, -93.2923),
    ("Columbia", "MO", 38.9517, -92.3341),
    ("Jefferson City", "MO", 38.5767, -92.1735),
    ("Joplin", "MO", 37.0842, -94.5133),
    ("Cape Girardeau", "MO", 37.3059, -89.5181),
    # Montana (7)
    ("Billings", "MT", 45.7833, -108.5007),
    ("Missoula", "MT", 46.8721, -113.9940),
    ("Great Falls", "MT", 47.5053, -111.3008),
    ("Bozeman", "MT", 45.6770, -111.0429),
    ("Butte", "MT", 46.0038, -112.5348),
    ("Helena", "MT", 46.5891, -112.0391),
    ("Kalispell", "MT", 48.1920, -114.3168),
    # Nebraska (6)
    ("Omaha", "NE", 41.2565, -95.9345),
    ("Lincoln", "NE", 40.8136, -96.7026),
    ("Grand Island", "NE", 40.9264, -98.3420),
    ("Kearney", "NE", 40.6993, -99.0817),
    ("North Platte", "NE", 41.1239, -100.7654),
    ("Scottsbluff", "NE", 41.8666, -103.6672),
    # Nevada (6)
    ("Las Vegas", "NV", 36.1699, -115.1398),
    ("Reno", "NV", 39.5296, -119.8138),
    ("Carson City", "NV", 39.1638, -119.7674),
    ("Elko", "NV", 40.8324, -115.7631),
    ("Winnemucca", "NV", 40.9730, -117.7357),
    ("Tonopah", "NV", 38.0672, -117.2300),
    # New Hampshire (4)
    ("Manchester", "NH", 42.9956, -71.4548),
    ("Nashua", "NH", 42.7654, -71.4676),
    ("Concord", "NH", 43.2081, -71.5376),
    ("Portsmouth", "NH", 43.0718, -70.7626),
    # New Jersey (6)
    ("Newark", "NJ", 40.7357, -74.1724),
    ("Jersey City", "NJ", 40.7178, -74.0431),
    ("Paterson", "NJ", 40.9168, -74.1718),
    ("Trenton", "NJ", 40.2171, -74.7429),
    ("Atlantic City", "NJ", 39.3643, -74.4229),
    ("Camden", "NJ", 39.9259, -75.1196),
    # New Mexico (6)
    ("Albuquerque", "NM", 35.0844, -106.6504),
    ("Las Cruces", "NM", 32.3199, -106.7637),
    ("Santa Fe", "NM", 35.6870, -105.9378),
    ("Roswell", "NM", 33.3943, -104.5230),
    ("Farmington", "NM", 36.7281, -108.2187),
    ("Clovis", "NM", 34.4048, -103.2052),
    # New York (9)
    ("New York", "NY", 40.7128, -74.0060),
    ("Buffalo", "NY", 42.8864, -78.8784),
    ("Rochester", "NY", 43.1566, -77.6088),
    ("Syracuse", "NY", 43.0481, -76.1474),
    ("Albany", "NY", 42.6526, -73.7562),
    ("Binghamton", "NY", 42.0987, -75.9180),
    ("Utica", "NY", 43.1009, -75.2327),
    ("Watertown", "NY", 43.9748, -75.9108),
    ("Plattsburgh", "NY", 44.6995, -73.4529),
    # North Carolina (8)
    ("Charlotte", "NC", 35.2271, -80.8431),
    ("Raleigh", "NC", 35.7796, -78.6382),
    ("Greensboro", "NC", 36.0726, -79.7920),
    ("Durham", "NC", 35.9940, -78.8986),
    ("Winston-Salem", "NC", 36.0999, -80.2442),
    ("Fayetteville", "NC", 35.0527, -78.8784),
    ("Wilmington", "NC", 34.2104, -77.8868),
    ("Asheville", "NC", 35.5951, -82.5515),
    # North Dakota (6)
    ("Fargo", "ND", 46.8772, -96.7898),
    ("Bismarck", "ND", 46.8083, -100.7837),
    ("Grand Forks", "ND", 47.9253, -97.0329),
    ("Minot", "ND", 48.2330, -101.2923),
    ("Williston", "ND", 48.1470, -103.6180),
    ("Dickinson", "ND", 46.8792, -102.7896),
    # Ohio (8)
    ("Columbus", "OH", 39.9612, -82.9988),
    ("Cleveland", "OH", 41.4993, -81.6944),
    ("Cincinnati", "OH", 39.1031, -84.5120),
    ("Toledo", "OH", 41.6528, -83.5379),
    ("Akron", "OH", 41.0814, -81.5190),
    ("Dayton", "OH", 39.7589, -84.1916),
    ("Youngstown", "OH", 41.0998, -80.6495),
    ("lima", "OH", 40.7425, -84.1052),
    # Oklahoma (6)
    ("Oklahoma City", "OK", 35.4676, -97.5164),
    ("Tulsa", "OK", 36.1540, -95.9928),
    ("Norman", "OK", 35.2226, -97.4395),
    ("Lawton", "OK", 34.6036, -98.3959),
    ("Enid", "OK", 36.3956, -97.8784),
    ("Ardmore", "OK", 34.1743, -97.1436),
    # Oregon (7)
    ("Portland", "OR", 45.5152, -122.6784),
    ("Eugene", "OR", 44.0521, -123.0868),
    ("Salem", "OR", 44.9429, -123.0351),
    ("Bend", "OR", 44.0582, -121.3153),
    ("Medford", "OR", 42.3265, -122.8756),
    ("Pendleton", "OR", 45.6721, -118.7886),
    ("Klamath Falls", "OR", 42.2249, -121.7817),
    # Pennsylvania (8)
    ("Philadelphia", "PA", 39.9526, -75.1652),
    ("Pittsburgh", "PA", 40.4406, -79.9959),
    ("Allentown", "PA", 40.6023, -75.4714),
    ("Erie", "PA", 42.1292, -80.0851),
    ("Harrisburg", "PA", 40.2732, -76.8867),
    ("Scranton", "PA", 41.4090, -75.6624),
    ("State College", "PA", 40.7934, -77.8600),
    ("Altoona", "PA", 40.5187, -78.3947),
    # Rhode Island (3)
    ("Providence", "RI", 41.8240, -71.4128),
    ("Warwick", "RI", 41.7001, -71.4162),
    ("Newport", "RI", 41.4901, -71.3128),
    # South Carolina (6)
    ("Charleston", "SC", 32.7765, -79.9311),
    ("Columbia", "SC", 34.0007, -81.0348),
    ("Greenville", "SC", 34.8526, -82.3940),
    ("Myrtle Beach", "SC", 33.6891, -78.8867),
    ("Florence", "SC", 34.1954, -79.7626),
    ("Spartanburg", "SC", 34.9496, -81.9320),
    # South Dakota (6)
    ("Sioux Falls", "SD", 43.5460, -96.7313),
    ("Rapid City", "SD", 44.0805, -103.2310),
    ("Aberdeen", "SD", 45.4647, -98.4865),
    ("Pierre", "SD", 44.3683, -100.3510),
    ("Watertown", "SD", 44.8994, -97.1151),
    ("Mitchell", "SD", 43.7094, -98.0298),
    # Tennessee (7)
    ("Nashville", "TN", 36.1627, -86.7816),
    ("Memphis", "TN", 35.1495, -90.0490),
    ("Knoxville", "TN", 35.9606, -83.9207),
    ("Chattanooga", "TN", 35.0456, -85.3097),
    ("Clarksville", "TN", 36.5298, -87.3595),
    ("Jackson", "TN", 35.6145, -88.8139),
    ("Johnson City", "TN", 36.3134, -82.3535),
    # Texas (15)
    ("Houston", "TX", 29.7604, -95.3698),
    ("San Antonio", "TX", 29.4241, -98.4936),
    ("Dallas", "TX", 32.7767, -96.7970),
    ("Austin", "TX", 30.2672, -97.7431),
    ("Fort Worth", "TX", 32.7555, -97.3308),
    ("El Paso", "TX", 31.7619, -106.4850),
    ("Corpus Christi", "TX", 27.8006, -97.3964),
    ("Lubbock", "TX", 33.5779, -101.8552),
    ("Laredo", "TX", 27.5036, -99.5076),
    ("Amarillo", "TX", 35.2220, -101.8313),
    ("Brownsville", "TX", 25.9017, -97.4975),
    ("Midland", "TX", 31.9973, -102.0779),
    ("Abilene", "TX", 32.4487, -99.7331),
    ("Beaumont", "TX", 30.0802, -94.1266),
    ("Wichita Falls", "TX", 33.9137, -98.4934),
    # Utah (6)
    ("Salt Lake City", "UT", 40.7608, -111.8910),
    ("Provo", "UT", 40.2338, -111.6585),
    ("Ogden", "UT", 41.2230, -111.9738),
    ("St. George", "UT", 37.0965, -113.5684),
    ("Logan", "UT", 41.7370, -111.8338),
    ("Moab", "UT", 38.5733, -109.5498),
    # Vermont (4)
    ("Burlington", "VT", 44.4759, -73.2121),
    ("Montpelier", "VT", 44.2601, -72.5754),
    ("Rutland", "VT", 43.6106, -72.9726),
    ("Brattleboro", "VT", 42.8509, -72.5579),
    # Virginia (7)
    ("Virginia Beach", "VA", 36.8529, -75.9780),
    ("Norfolk", "VA", 36.8508, -76.2859),
    ("Richmond", "VA", 37.5407, -77.4360),
    ("Roanoke", "VA", 37.2710, -79.9414),
    ("Charlottesville", "VA", 38.0293, -78.4767),
    ("Alexandria", "VA", 38.8048, -77.0469),
    ("Lynchburg", "VA", 37.4138, -79.1422),
    # Washington (7)
    ("Seattle", "WA", 47.6062, -122.3321),
    ("Spokane", "WA", 47.6588, -117.4260),
    ("Tacoma", "WA", 47.2529, -122.4443),
    ("Olympia", "WA", 47.0379, -122.9007),
    ("Yakima", "WA", 46.6021, -120.5059),
    ("Kennewick", "WA", 46.2087, -119.1199),
    ("Bellingham", "WA", 48.7519, -122.4787),
    # West Virginia (5)
    ("Charleston", "WV", 38.3498, -81.6326),
    ("Huntington", "WV", 38.4192, -82.4452),
    ("Morgantown", "WV", 39.6295, -79.9559),
    ("Wheeling", "WV", 40.0640, -80.7209),
    ("Beckley", "WV", 37.7782, -81.1882),
    # Wisconsin (7)
    ("Milwaukee", "WI", 43.0389, -87.9065),
    ("Madison", "WI", 43.0731, -89.4012),
    ("Green Bay", "WI", 44.5133, -88.0133),
    ("Eau Claire", "WI", 44.8113, -91.4985),
    ("La Crosse", "WI", 43.8014, -91.2396),
    ("Wausau", "WI", 44.9591, -89.6301),
    ("Superior", "WI", 46.7208, -92.1041),
    # Wyoming (6)
    ("Cheyenne", "WY", 41.1400, -104.8202),
    ("Casper", "WY", 42.8501, -106.3252),
    ("Laramie", "WY", 41.3114, -105.5911),
    ("Gillette", "WY", 44.2911, -105.5022),
    ("Rock Springs", "WY", 41.5875, -109.2029),
    ("Jackson", "WY", 43.4799, -110.7624),
]

assert len(RAW_CITIES) == 336, f"Expected 336 cities, got {len(RAW_CITIES)}"


def albers_usa_project(
    lat: float, lon: float, state: str, width: float = 1200.0, height: float = 750.0
) -> tuple[float, float]:
    """Projects (latitude, longitude) onto a 1200x750 SVG canvas using Albers USA projection.

    Uses standard parallels 29.5N and 45.5N, central meridian -96W, central latitude 37.5N
    for the contiguous 48 states, and dedicated inset boxes for Alaska and Hawaii.
    """
    if state == "AK":
        # Alaska inset in bottom-left region (x: 60..215, y: 560..700)
        # Alaska bounds roughly lat 55..66, lon -155..-132
        norm_x = (lon - (-155.0)) / (-132.0 - (-155.0))
        norm_y = (66.5 - lat) / (66.5 - 55.0)
        x = 65.0 + max(0.0, min(1.0, norm_x)) * 150.0
        y = 565.0 + max(0.0, min(1.0, norm_y)) * 130.0
        return round(x, 2), round(y, 2)

    if state == "HI":
        # Hawaii inset in bottom-left region next to Alaska (x: 245..365, y: 615..710)
        # Hawaii bounds roughly lat 19..22.5, lon -160..-154.5
        norm_x = (lon - (-160.0)) / (-154.5 - (-160.0))
        norm_y = (22.5 - lat) / (22.5 - 19.0)
        x = 250.0 + max(0.0, min(1.0, norm_x)) * 115.0
        y = 620.0 + max(0.0, min(1.0, norm_y)) * 85.0
        return round(x, 2), round(y, 2)

    # Standard Albers Equal-Area Conic for Contiguous US
    phi1 = math.radians(29.5)
    phi2 = math.radians(45.5)
    phi0 = math.radians(37.5)
    lam0 = math.radians(-96.0)

    phi = math.radians(lat)
    lam = math.radians(lon)

    n = 0.5 * (math.sin(phi1) + math.sin(phi2))
    c = math.cos(phi1) ** 2 + 2.0 * n * math.sin(phi1)
    rho0 = math.sqrt(c - 2.0 * n * math.sin(phi0)) / n
    rho = math.sqrt(max(0.0, c - 2.0 * n * math.sin(phi))) / n
    theta = n * (lam - lam0)

    raw_x = rho * math.sin(theta)
    raw_y = rho0 - rho * math.cos(theta)

    # Scale to fit 1200x750 canvas cleanly with margins
    scale = 1380.0
    svg_x = (width * 0.505) + raw_x * scale
    svg_y = (height * 0.52) - raw_y * scale
    return round(svg_x, 2), round(svg_y, 2)


def get_cities_dataset() -> list[dict[str, Any]]:
    """Returns the structured list of 336 US cities with projected SVG coordinates."""
    cities: list[dict[str, Any]] = []
    for idx, (name, state, lat, lon) in enumerate(RAW_CITIES):
        # Fix capitalization on Lima, OH if needed
        clean_name = "Lima" if name == "lima" else name
        svg_x, svg_y = albers_usa_project(lat, lon, state)
        cities.append(
            {
                "id": idx,
                "name": clean_name,
                "state": state,
                "label": f"{clean_name}, {state}",
                "latitude": lat,
                "longitude": lon,
                "svg_x": svg_x,
                "svg_y": svg_y,
            }
        )
    return cities
