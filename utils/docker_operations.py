import subprocess
import sys
from datetime import datetime

from pipeline_utils import *


def build_and_push_docker_images(docker_folder_path, docker_username, docker_token):
    today = datetime.now().strftime("%Y.%m.%d")
    date_tag_suffix = "-alt"
    docker_image_names = get_docker_image_names(docker_folder_path)

    try:
        # Docker login
        login_command = f"echo {docker_token} | docker login -u {docker_username} --password-stdin"
        subprocess.run(login_command, shell=True, check=True)

        for image_name in docker_image_names:
            date_tag = f"{docker_username}/{image_name}:v{today}{date_tag_suffix}"
            latest_tag = f"{docker_username}/{image_name}:latest"

            # Build the Docker image with the date-based tag
            build_command = f"docker build -t {date_tag} {docker_folder_path}/{image_name}"
            print(f"Building image: {date_tag}")
            subprocess.run(build_command, shell=True, check=True)

            # Push the date-based tagged image
            push_command_date = f"docker push {date_tag}"
            print(f"Pushing image: {date_tag}")
            subprocess.run(push_command_date, shell=True, check=True)

            # Tag the newly built image as 'latest'
            retag_command = f"docker tag {date_tag} {latest_tag}"
            print(f"Tagging {date_tag} as {latest_tag}")
            subprocess.run(retag_command, shell=True, check=True)

            # Push the 'latest' tagged image
            push_command_latest = f"docker push {latest_tag}"
            print(f"Pushing image: {latest_tag}")
            subprocess.run(push_command_latest, shell=True, check=True)

            # Remove the images locally to free up disk space
            remove_command_date = f"docker rmi {date_tag}"
            print(f"Removing image: {date_tag}")
            subprocess.run(remove_command_date, shell=True, check=True)

            remove_command_latest = f"docker rmi {latest_tag}"
            print(f"Removing image: {latest_tag}")
            subprocess.run(remove_command_latest, shell=True, check=True)

            print(f"Successfully processed: {date_tag} and {latest_tag}")

        # If we reach this point, we have successfully built and pushed today's images.
        # Set the output variable to the date-based version tag (e.g., v2024.12.19-alt).
        # This assumes all images use the same date tag.
        print(f"::set-output name=docker_version::v{today}{date_tag_suffix}")

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
