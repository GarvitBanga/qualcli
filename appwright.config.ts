
                import { defineConfig, Platform } from "appwright";
                export default defineConfig({
                    projects: [{"name": "android", "use": {"platform": "ANDROID", "device": {"provider": "emulator"}, "buildPath": "apps/xyz123.apk"}}]
                });
                