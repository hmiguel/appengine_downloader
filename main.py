import yaml, io
import zipfile, argparse, subprocess
from google.cloud import storage

def run_command(command):
    p = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
    return p.stdout.read().decode('utf-8')

def set_project(project_id):
    output = run_command(f'gcloud config set project {project_id}')
    if('WARNING' in output):
        raise Exception(output.split('WARNING')[1])

def get_metadata(version_id):
    metadata = run_command(f'gcloud app versions describe {version_id} -s default')
    if 'ERROR' in metadata:
        raise Exception(metadata.split('ERROR')[1])
    return yaml.safe_load(metadata)

def get_file(bucket, sha1Sum):
    blob = bucket.blob(sha1Sum)
    return blob.download_as_string()

def download_files(project_id, files):
    storage_client = storage.Client(project_id)
    bucket = storage_client.get_bucket(f"staging.{project_id}.appspot.com")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for filename in files.keys():
            content = get_file(bucket, files[filename].get('sha1Sum'))
            zip_file.writestr(filename, content)
    return buffer

def save_zip(zip_buffer, name):
    with open(f"{name}.zip", 'wb') as f:
        f.write(zip_buffer.getvalue())

def main(version_id, project_id):
    if project_id:
        print(f"Setting project to {project_id}...")
        set_project(project_id)

    print(f"Getting metadata of version '{version_id}'...")
    data = get_metadata(version_id)

    project_id = data['name'].split('/')[1]
    files = data.get('deployment').get('files')

    print("Downloading files...")
    zip_buffer = download_files(project_id, files)

    print(f"Saving zip '{version_id}.zip'...")
    save_zip(zip_buffer, version_id)

    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--project", help = "Set Project")
    parser.add_argument("-v", "--version", help = "Set Version")
    args = parser.parse_args()
    main(args.version, args.project)