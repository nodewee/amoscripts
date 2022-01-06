from fake_builtin import *

# ========== Script Settings  ==========
# script executor configurations
config = {
    "runtime": "amopy0.2",  # Options: amopy0.2
    "timeout": 30,  # Unit: Second. Options: 30, 60, 120, 180
}
# script argument options
arguments = [
    {
        "label": "APY greater than",
        "hint": "年化收益率大于",
        "key": "apy>",
        "type": "number",
        "value": 1,
    },
    {
        "label": "Volatility greater than",
        "hint": "APY波动变化大于",
        "key": "vol>",
        "type": "number",
        "value": 0,
    },
]
# type 可选: string, number, time, datetime


# ========== Program  ==========
def program():

    data_file_name = "pando_rings_supply_apy.json"

    def get_pando_rings_markets_data():
        """
        - Parameters
            - asset_symbols, example: "USDT,BTC,ETH". default is "*" means all assets
            - asset_symbols, percentage number, 0~100.
        """

        log("Get markets data from pando rings ...")
        PandoRings_API_EndPoint = "https://rings-api.pando.im/api/v1/"
        url = PandoRings_API_EndPoint + "markets/all"
        ok, rsp = http_get_with_json(url)

        if not ok or "data" not in rsp:
            err_msg = f"{rsp}"
            return False, err_msg

        return True, rsp["data"]

    def filter_markets(
        markets: list, asset_symbols="*", apy_threshold=0, floating_point=0
    ):
        """return asset_apy_mapping"""
        log("filtering...")

        # filter by asset symbol
        keep_assets = None
        if asset_symbols != "*":
            keep_assets = [x.strip().upper() for x in asset_symbols.split(",")]

        # calc supply apy
        asset_apy_mapping = {}
        for item in markets:
            symbol = item["symbol"].upper()
            # filter by assets
            if keep_assets is not None:
                if symbol not in keep_assets:
                    continue
            # apy number
            supply_apy = float(item["supply_apy"])
            percent = int(supply_apy * 10000) / 100
            # filter by apy threshold
            if percent > apy_threshold:
                asset_apy_mapping[symbol] = percent

        if len(asset_apy_mapping) == 0:
            return asset_apy_mapping  # {}

        # filter by floating_point
        will_notice = True
        if floating_point > 0:
            will_notice = False
            # any assets apy floating greater than point, will notice
            ok, r = amocf_storage_load(data_file_name)
            if not ok:
                log(f"amocf_storage_load failed: {r}")
            if ok:
                last_assets_apy = r
                for symbol in last_assets_apy:
                    if symbol in asset_apy_mapping:
                        if (
                            abs(asset_apy_mapping[symbol] - last_assets_apy[symbol])
                            > floating_point
                        ):
                            will_notice = True
                            break

        if will_notice:
            return asset_apy_mapping
        else:
            return {}

    def send_mixin_msg(text):
        log("send mixin message")
        # text = "🤖️PandoRingsSupplyAPY:\n" + text
        text = _env["APPLET_TITLE"] + "\n" + text
        amocf_send_me_mmmsg_text(text)

    def render_report(asset_apy_mapping):
        def get_emoji(percent):
            if percent < 4:
                return ""
            if percent < 8:
                return "🧧"
            if percent < 15:
                return "🤑🤑"
            # bigger
            return "💥💥💥"

        lines = []
        for symbol in asset_apy_mapping:
            percent = asset_apy_mapping[symbol]
            line = f"{symbol} {percent}% {get_emoji(percent)}"
            lines.append(line)
        report_text = "\n".join(lines)

        return report_text

    ok, rsp = get_pando_rings_markets_data()
    if not ok:
        log(f"Failed to get pando rings markets data: {rsp}")
        return

    asset_apy_mapping = filter_markets(rsp, "*", _args["apy>"], _args["vol>"])
    if len(asset_apy_mapping) == 0:
        log("no matched assets")
        return
    log(f"matched {len(asset_apy_mapping)}")

    text = render_report(asset_apy_mapping)
    send_mixin_msg(text)

    dataname = amocf_storage_save(asset_apy_mapping, data_file_name)
    if dataname:
        log("Saved current apy.")
        log(dataname)
    else:
        log("Failed to save current apy.")
