import zipfile
import shutil
import os

zip_path = "./builds/wikipedia_ios.zip"
extracted_folder = "./builds/wikipedia_ios.app"
app_source = os.path.join(extracted_folder, "Wikipedia.app")
app_dest = "./builds/Wikipedia.app"

def extract_app():
    try:
        print(f"📦 Unzipping {zip_path} ...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extracted_folder)

        if os.path.exists(app_dest):
            print("🧹 Removing previous Wikipedia.app ...")
            shutil.rmtree(app_dest)

        print(f"📁 Copying {app_source} → {app_dest}")
        shutil.copytree(app_source, app_dest)

        print(f"🧽 Cleaning up {extracted_folder}")
        shutil.rmtree(extracted_folder)

        print("✅ Extraction complete")
    except Exception as e:
        print(f"❌ extract_app: {e}")

if __name__ == "__main__":
    extract_app()
