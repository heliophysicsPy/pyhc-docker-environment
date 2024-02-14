import subprocess
import sys
from datetime import datetime

from pipeline_utils import *


def build_and_push_docker_images(docker_folder_path, docker_username, docker_token):
    today = datetime.now().strftime("%Y.%m.%d")
    docker_image_names = get_docker_image_names(docker_folder_path)

    try:
        # Docker login
        login_command = f"echo {docker_token} | docker login -u {docker_username} --password-stdin"
        subprocess.run(login_command, shell=True, check=True)

        for image_name in docker_image_names:
            tag = f"{docker_username}/{image_name}:v{today}"

            # Build the Docker image
            build_command = f"docker build -t {tag} {docker_folder_path}/{image_name}"
            print(f"Building image: {tag}")
            subprocess.run(build_command, shell=True, check=True)

            # Push the Docker image
            push_command = f"docker push {tag}"
            print(f"Pushing image: {tag}")
            subprocess.run(push_command, shell=True, check=True)

            # Remove the Docker image to free up disk space
            remove_command = f"docker rmi {tag}"
            print(f"Removing image: {tag}")
            subprocess.run(remove_command, shell=True, check=True)

            print(f"Successfully processed: {tag}")

    except subprocess.CalledProcessError as e:
        print(f"Error during Docker operations: {e}", flush=True)
        print("::set-output name=should_run::false", flush=True)
        sys.exit(1)  # Exit the script with an error status
    except Exception as e:
        print(f"Unhandled exception: {e}", flush=True)
        print("::set-output name=should_run::false", flush=True)
        sys.exit(1)  # Exit the script with an error status


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: docker_operations.py <docker_folder_path> <docker_username> <docker_token>")
        sys.exit(1)

    docker_folder = sys.argv[1]  # Path to the docker folder in the repository
    username = sys.argv[2]       # Docker Hub username
    token = sys.argv[3]          # Docker Hub token
    build_and_push_docker_images(docker_folder, username, token)
