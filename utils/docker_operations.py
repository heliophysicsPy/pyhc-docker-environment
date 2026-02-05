import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from .pipeline_utils import *
except ImportError:
    from pipeline_utils import *


def copy_packages_to_contents(docker_folder_path, image_name, packages_file=None):
    """Copy packages.txt to the Docker image's contents folder before building.

    Args:
        docker_folder_path: Path to the docker folder (e.g., ./docker)
        image_name: Name of the Docker image folder (e.g., pyhc-environment)
        packages_file: Path to packages.txt (default: repo root packages.txt)
    """
    if packages_file is None:
        # Default to repo root packages.txt (relative to this script's location)
        packages_file = Path(__file__).parent.parent / "packages.txt"

    packages_file = Path(packages_file)
    contents_dir = Path(docker_folder_path) / image_name / "contents"
    dest_file = contents_dir / "packages.txt"

    if not packages_file.exists():
        print(f"Warning: packages.txt not found at {packages_file}")
        return False

    if not contents_dir.exists():
        print(f"Warning: contents directory not found at {contents_dir}")
        return False

    shutil.copy(packages_file, dest_file)
    print(f"Copied {packages_file} to {dest_file}")
    return dest_file


def remove_packages_from_contents(docker_folder_path, image_name):
    """Remove packages.txt from the Docker image's contents folder after building.

    Args:
        docker_folder_path: Path to the docker folder (e.g., ./docker)
        image_name: Name of the Docker image folder (e.g., pyhc-environment)
    """
    dest_file = Path(docker_folder_path) / image_name / "contents" / "packages.txt"

    if dest_file.exists():
        dest_file.unlink()
        print(f"Removed {dest_file}")


def build_and_push_docker_images(docker_folder_path, docker_username, docker_token, packages_file=None):
    """Build and push Docker images to Docker Hub.

    Args:
        docker_folder_path: Path to the docker folder containing image subdirectories
        docker_username: Docker Hub username
        docker_token: Docker Hub access token
        packages_file: Optional path to packages.txt (default: repo root)
    """
    today = datetime.now().strftime("%Y.%m.%d")
    docker_image_names = get_docker_image_names(docker_folder_path)
    images_with_packages = []  # Track which images had packages.txt copied

    try:
        # Docker login
        login_command = f"echo {docker_token} | docker login -u {docker_username} --password-stdin"
        subprocess.run(login_command, shell=True, check=True)

        for image_name in docker_image_names:
            # Copy packages.txt to contents folder before building
            if copy_packages_to_contents(docker_folder_path, image_name, packages_file):
                images_with_packages.append(image_name)
            date_tag = f"{docker_username}/{image_name}:v{today}"
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
        # Set the output variable to the date-based version tag (e.g., v2024.12.19).
        # This assumes all images use the same date tag.
        set_github_output("docker_version", f"v{today}")

    except subprocess.CalledProcessError as e:
        print(f"Error during Docker operations: {e}", flush=True)
        set_github_output("should_run", "false")
        sys.exit(1)  # Exit the script with an error status
    except Exception as e:
        print(f"Unhandled exception: {e}", flush=True)
        set_github_output("should_run", "false")
        sys.exit(1)  # Exit the script with an error status
    finally:
        # Clean up: remove packages.txt from contents folders
        for image_name in images_with_packages:
            remove_packages_from_contents(docker_folder_path, image_name)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: docker_operations.py <docker_folder_path> <docker_username> <docker_token>")
        sys.exit(1)

    docker_folder = sys.argv[1]  # Path to the docker folder in the repository
    username = sys.argv[2]       # Docker Hub username
    token = sys.argv[3]          # Docker Hub token
    build_and_push_docker_images(docker_folder, username, token)
