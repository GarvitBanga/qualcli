
                import { defineConfig, Platform } from "appwright";
                import path from "path";

                export default defineConfig({
                    projects: [{"name": "android", "use": {"platform": Platform.ANDROID, "device": {"provider": "browserstack", "name": "Google Pixel 7", "osVersion": "13.0"}, 
                        // "buildPath": "bs://f45540331eecc2143e0d1e643e35b73e5ed68363",
                        buildPath: path.join("builds", "wikipedia.apk")
                    
                    }}
                    // ,
                    // {
                    //     "name": "ios",
                    //     "use": {
                    //         "platform": Platform.IOS,
                    //         "device": {
                    //             "provider": "browserstack",
                    //             "name": "iPhone 14 Pro",
                    //             "osVersion": "16"
                    //         },
                    //         buildPath: path.join("builds", "wikipedia_ios.zip")
                    //         // buildPath: "bs://store:com.wikimedia.wikipedia"
                    //     }
                    // }
                ]
                });
                