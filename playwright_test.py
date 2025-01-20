from playwright.sync_api import sync_playwright
import time
import random
import platform

def get_chrome_version():
    return "121.0.0.0"

def get_platform_specific_configs():
    os_name = platform.system()
    if os_name == "Windows":
        return {
            "platform": "Windows",
            "userAgent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{get_chrome_version()} Safari/537.36",
            "gpu": "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
            "vendor": "Google Inc. (Intel)",
        }
    elif os_name == "Darwin":
        return {
            "platform": "MacIntel",
            "userAgent": f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{get_chrome_version()} Safari/537.36",
            "gpu": "ANGLE (Intel, Intel(R) Iris(TM) Plus Graphics OpenGL Engine, OpenGL 4.1)",
            "vendor": "Google Inc. (Apple)",
        }
    else:  # Linux
        return {
            "platform": "Linux",
            "userAgent": f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{get_chrome_version()} Safari/537.36",
            "gpu": "ANGLE (Intel, Mesa Intel(R) UHD Graphics 620 (KBL GT2), OpenGL 4.6)",
            "vendor": "Google Inc. (Intel)",
        }

def main():
    platform_configs = get_platform_specific_configs()
    
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=False,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-automation',
            '--disable-infobars',
            '--start-maximized',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-blink-features',
            '--ignore-certificate-errors',
            f'--user-agent={platform_configs["userAgent"]}',
            '--window-size=1920,1080',
            '--enable-audio-service-sandbox',
            '--enable-font-antialiasing',
            '--force-color-profile=srgb',
            '--disable-features=IsolateOrigins,site-per-process',
            '--enable-features=NetworkService,NetworkServiceInProcess'
        ]
    )

    context = browser.new_context(
        viewport=None,
        user_agent=platform_configs["userAgent"],
        locale="en-US",
        timezone_id="America/New_York",
        geolocation={"latitude": 40.7128, "longitude": -74.0060},
        permissions=["geolocation", "notifications", "midi", "camera", "microphone", "clipboard-read", "clipboard-write"],
        color_scheme='light',
        device_scale_factor=1,
        is_mobile=False,
        has_touch=False,
        accept_downloads=True,
        ignore_https_errors=True,
        extra_http_headers={
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'sec-ch-ua': f'"Not A(Brand";v="99", "Google Chrome";v="{get_chrome_version()}", "Chromium";v="{get_chrome_version()}"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': f'"{platform_configs["platform"]}"'
        }
    )

    page = context.new_page()

    # Inject common browser APIs and properties
    page.evaluate("""() => {
        Object.defineProperties(navigator, {
            webdriver: { get: () => undefined },
            languages: { get: () => ['en-US', 'en'] },
            plugins: { get: () => [
                { description: "Portable Document Format", filename: "internal-pdf-viewer", name: "Chrome PDF Plugin" },
                { description: "", filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai", name: "Chrome PDF Viewer" },
                { description: "", filename: "internal-nacl-plugin", name: "Native Client" }
            ]},
            vendor: { get: () => '""" + platform_configs["vendor"] + """' },
            platform: { get: () => '""" + platform_configs["platform"] + """' }
        });

        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };

        // Add WebGL properties
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return '""" + platform_configs["gpu"] + """';
            }
            if (parameter === 37446) {
                return '""" + platform_configs["vendor"] + """';
            }
            return getParameter.apply(this, arguments);
        };
    }""")


    # Navigate to website
    page.goto('https://example.com', wait_until='networkidle')

    try:
        print("Browser is open. Press Ctrl+C to close...")
    except KeyboardInterrupt:
        print("\nClosing browser...")
        context.close()
        browser.close()
        playwright.stop()

if __name__ == "__main__":
    main()