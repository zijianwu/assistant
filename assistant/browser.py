from playwright.sync_api import sync_playwright
import platform
from pathlib import Path
from typing import Dict, Optional, bool
import random

class BrowserPage:
    """A wrapper around Playwright's Page object that maintains BrowserManager context."""
    
    def __init__(self, playwright_page):
        """
        Initialize the managed page.
        
        Args:
            playwright_page: The underlying Playwright page object
            browser_manager: The BrowserManager instance that created this page
        """
        self._page = playwright_page
        
    def __getattr__(self, name):
        """Delegate any unknown attributes to the underlying Playwright page."""
        return getattr(self._page, name)
    
    def __repr__(self):
        return f"<BrowserPage wrapper of Playwright Page"


class BrowserManager:
    """Manages a persistent Playwright browser instance with realistic user profile."""
    
    def __init__(self, 
                 user_data_dir: Optional[str] = None,
                 debug: bool = False):
        """
        Initialize the browser manager with a consistent user profile.
        
        Args:
            user_data_dir: Directory to store persistent browser data. If None,
                         defaults to './browser_data'.
        """
        self.user_data_dir = Path(user_data_dir or './browser_data')
        self.user_data_dir.mkdir(exist_ok=True)
        self.playwright = None
        self.browser_context = None
        self.debug = debug
        
        # Developer persona configuration
        self.timezone = "America/New_York"
        self.base_latitude = 42.3601  # Boston
        self.base_longitude = -71.0589
        self.languages = ['en-US', 'en']
        self.developer_extensions = [
            { "name": "React Developer Tools", "filename": "fmkadmapgofadopljbjfkapdkoienihi" },
            { "name": "Redux DevTools", "filename": "lmhkpmbekcpmknklioeibfkpmmfibljd" },
            { "name": "JSON Formatter", "filename": "bcjindcccaagfpapjjmafapmmgkkhgoa" },
            { "name": "GitHub Dark Theme", "filename": "kom08lmcnfglkjfggdepcdcpbgkmegjj" }
        ]

    def _get_chrome_version(self) -> str:
        """Get a realistic Chrome version."""
        major_version = 121  # Base version
        minor_versions = [f"{random.randint(0, 9)}" for _ in range(3)]
        return f"{major_version}.{'.'.join(minor_versions)}"

    def _get_platform_specific_configs(self) -> Dict[str, str]:
        """Get platform-specific browser configurations for our developer persona."""
        chrome_version = self._get_chrome_version()
        
        # Focused on MacOS configuration since our persona uses a MacBook Pro
        configs = {
            "Darwin": {
                "platform": "MacIntel",
                "userAgent": f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36",
                "gpu": "ANGLE (Apple, Apple M1 Pro, OpenGL 4.1)",
                "vendor": "Google Inc. (Apple)",
                "screen": {
                    "width": 2560,
                    "height": 1600,
                    "scale_factor": 2,  # Retina display
                },
                "hardware_concurrency": 10,  # M1 Pro typical value
                "device_memory": 32,  # GB
            }
        }
        
        # Fallback configurations for other platforms
        default_config = configs["Darwin"]
        return configs.get(platform.system(), default_config)

    def _inject_browser_apis(self, page) -> None:
        """Inject realistic browser APIs and developer-specific configurations."""
        platform_configs = self._get_platform_specific_configs()
        
        # Add developer-specific WebGL extensions
        webgl_extensions = [
            'ANGLE_instanced_arrays',
            'EXT_blend_minmax',
            'EXT_color_buffer_half_float',
            'EXT_disjoint_timer_query',
            'EXT_float_blend',
            'EXT_frag_depth',
            'EXT_shader_texture_lod',
            'EXT_texture_compression_bptc',
            'EXT_texture_compression_rgtc',
            'EXT_texture_filter_anisotropic',
            'EXT_sRGB',
            'KHR_parallel_shader_compile',
            'OES_element_index_uint',
            'OES_fbo_render_mipmap',
            'OES_standard_derivatives',
            'OES_texture_float',
            'OES_texture_float_linear',
            'OES_texture_half_float',
            'OES_texture_half_float_linear',
            'OES_vertex_array_object',
            'WEBGL_color_buffer_float',
            'WEBGL_compressed_texture_s3tc',
            'WEBGL_compressed_texture_s3tc_srgb',
            'WEBGL_debug_renderer_info',
            'WEBGL_debug_shaders',
            'WEBGL_depth_texture',
            'WEBGL_draw_buffers',
            'WEBGL_lose_context',
            'WEBGL_multi_draw'
        ]

        page.evaluate("""(configs) => {
            // Generate a random ID without using crypto.randomUUID
            const generateRandomId = () => {
                const hex = '0123456789abcdef';
                let id = '';
                for (let i = 0; i < 32; i++) {
                    id += hex[Math.floor(Math.random() * 16)];
                    if ([8, 12, 16, 20].includes(i)) id += '-';
                }
                return id;
            };

            // Simulate developer-specific browser environment
            Object.defineProperties(navigator, {
                webdriver: { get: () => undefined },
                languages: { get: () => configs.languages },
                hardwareConcurrency: { get: () => configs.hardware_concurrency },
                deviceMemory: { get: () => configs.device_memory },
                platform: { get: () => configs.platform },
                vendor: { get: () => configs.vendor },
                plugins: { get: () => configs.extensions.map(ext => ({
                    description: "Chrome Extension",
                    filename: ext.filename,
                    name: ext.name
                }))},
                connection: { get: () => ({
                    effectiveType: '4g',
                    rtt: 50,
                    downlink: 10,
                    saveData: false
                })}
            });

            // Add developer tools detection
            window.devToolsOpened = false;
            const devTools = {
                get isOpen() {
                    return window.devToolsOpened;
                }
            };
            Object.defineProperty(window, 'devtools', { get: () => devTools });

            // Realistic Chrome runtime
            window.chrome = {
                runtime: {
                    id: generateRandomId(),
                    getManifest: () => ({ manifest_version: 3 }),
                    connect: () => ({
                        onMessage: { addListener: () => {} },
                        postMessage: () => {}
                    })
                },
                app: { isInstalled: false },
                csi: () => ({ startE: Date.now(), onloadT: Date.now() + 100 }),
                loadTimes: () => ({
                    firstPaintTime: Date.now(),
                    firstPaintAfterLoadTime: Date.now() + 100,
                    wasNpnNegotiated: true,
                    wasAlternateProtocolAvailable: true,
                    connectionInfo: "h2"
                })
            };

            // WebGL enhancements
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return configs.gpu;
                }
                if (parameter === 37446) {
                    return configs.vendor;
                }
                return getParameter.apply(this, arguments);
            };

            // Add WebGL extensions
            const getExtension = WebGLRenderingContext.prototype.getExtension;
            WebGLRenderingContext.prototype.getExtension = function(extension) {
                if (configs.webgl_extensions.includes(extension)) {
                    return {};
                }
                return getExtension.apply(this, arguments);
            };
        }""", {
            "platform": platform_configs["platform"],
            "vendor": platform_configs["vendor"],
            "gpu": platform_configs["gpu"],
            "languages": self.languages,
            "extensions": self.developer_extensions,
            "hardware_concurrency": platform_configs["hardware_concurrency"],
            "device_memory": platform_configs["device_memory"],
            "webgl_extensions": webgl_extensions
        })

    def start(self) -> BrowserPage:
        """Initializes and launches a new browser instance

        Returns:
            BrowserPage: A new browser page instance ready for automation.

        Example:
            ```python
            browser = Browser(debug=True)
            page = browser.start()
            ```
        """
        if self.browser_context is not None:
            return

        platform_configs = self._get_platform_specific_configs()
        self.playwright = sync_playwright().start()
        
        # Calculate location with slight randomization for realism
        latitude = self.base_latitude + random.uniform(-0.01, 0.01)
        longitude = self.base_longitude + random.uniform(-0.01, 0.01)
        
        # Launch with developer-focused configuration
        self.browser_context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.user_data_dir),
            headless=not self.debug,
            viewport=platform_configs["screen"],
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-automation',
                '--disable-infobars',
                '--start-maximized',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--ignore-certificate-errors',
                f'--user-agent={platform_configs["userAgent"]}',
                f'--window-size={platform_configs["screen"]["width"]},{platform_configs["screen"]["height"]}',
                '--enable-audio-service-sandbox',
                '--enable-font-antialiasing',
                '--force-color-profile=srgb',
                '--disable-features=IsolateOrigins',
                '--enable-features=NetworkService,NetworkServiceInProcess,NativeNotifications',
                '--password-store=basic',
                '--enable-parallel-downloading',
                '--enable-javascript-harmony',
                '--enable-experimental-web-platform-features',
                '--enable-gpu-rasterization',
                '--enable-oop-rasterization',
                '--enable-zero-copy',
                '--ignore-gpu-blocklist'
            ],
            user_agent=platform_configs["userAgent"],
            locale="en-US",
            timezone_id=self.timezone,
            geolocation={"latitude": latitude, "longitude": longitude},
            permissions=["geolocation", "notifications", "midi", "camera", "microphone", 
                        "clipboard-read", "clipboard-write", "payment-handler",
                        "accelerometer", "ambient-light-sensor"],
            color_scheme='dark',  # Developers often prefer dark mode
            device_scale_factor=platform_configs["screen"]["scale_factor"],
            is_mobile=False,
            has_touch=True,  # Modern MacBooks have touch bars
            accept_downloads=True,
            ignore_https_errors=True,
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'DNT': '1',  # Privacy-conscious developer
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'sec-ch-ua': f'"Not A(Brand";v="99", "Google Chrome";v="{self._get_chrome_version()}", "Chromium";v="{self._get_chrome_version()}"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': f'"{platform_configs["platform"]}"',
                'sec-ch-ua-arch': '"arm"',  # M1 Pro architecture
                'sec-ch-ua-bitness': '"64"',
                'sec-ch-ua-full-version': f'"{self._get_chrome_version()}"',
                'sec-ch-ua-platform-version': '"13.0.0"'  # macOS version
            }
        )
        
        # Set longer timeout for development workflows
        if self.debug:
            self.browser_context.set_default_timeout(36_000_000)
        else:
            self.browser_context.set_default_timeout(10_000)  # 10 seconds

        page = self._new_page()
        return page

    def stop(self) -> None:
        """Stops and cleans up browser automation resources.
    
        Closes any active browser context and stops the Playwright instance.
        After calling this method, browser_context and playwright attributes
        will be set to None.

        Example:
            >>> browser = Browser()
            >>> browser.start()
            >>> # ... do browser automation ...
            >>> browser.stop()  # cleanup resources
        
        Returns:
            None
        """
        if self.browser_context:
            self.browser_context.close()
        if self.playwright:
            self.playwright.stop()
            
        self.browser_context = None
        self.playwright = None

    def _new_page(self):
        """Get a new page with injected browser APIs and developer tools."""
        if not self.browser_context:
            raise RuntimeError("Browser context not initialized. Call start() first.")
        
        page = self.browser_context.new_page()
        self._inject_browser_apis(page)
        page = BrowserPage(page)
        return page


