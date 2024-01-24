import subprocess
import sys
from datetime import datetime

from pipeline_utils import *


def build_and_push_docker_images(docker_folder_path, docker_username, docker_token):
    today = datetime.now().strftime("%Y.%m.%d")
    docker_image_names = get_docker_image_names(docker_folder_path)
    build_commands = []
    push_commands = []

    for image_name in docker_image_names:
        tag = f"{docker_username}/{image_name}:v{today}"
        build_commands.append(f"docker build -t {tag} {docker_folder_path}/{image_name}")
        push_commands.append(f"docker push {tag}")

    try:
        # Docker login
        login_command = f"echo {docker_token} | docker login -u {docker_username} --password-stdin"
        subprocess.run(login_command, shell=True, check=True)

        # Docker build
        for build_command in build_commands:
            subprocess.run(build_command, shell=True, check=True)

        # Docker push
        for push_command in push_commands:
            subprocess.run(push_command, shell=True, check=True)
            print(f"Successfully pushed: `{push_command}`")

    except subprocess.CalledProcessError as e:
        print(f"Error during Docker operations: {e}")
        sys.exit(1)  # Exit the script with an error status

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: docker_operations.py <docker_folder_path> <docker_username> <docker_token>")
        sys.exit(1)

    docker_folder = sys.argv[1]  # Path to the docker folder in the repository
    username = sys.argv[2]       # Docker Hub username
    token = sys.argv[3]          # Docker Hub token
    build_and_push_docker_images(docker_folder, username, token)
