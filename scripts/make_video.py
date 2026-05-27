import cv2
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="Stitch image frames into a video for VO testing.")
    parser.add_argument("-i", "--input", type=str, required=True, 
                        help="Path to the input folder with frames (e.g., dataset_frames/)")
    parser.add_argument("-o", "--output", type=str, default="output_dataset.mp4", 
                        help="Name of the output video file (default: output_dataset.mp4)")

    args = parser.parse_args()

    image_folder = args.input
    video_name = args.output

    if not os.path.exists(image_folder):
        print(f"Error: Directory '{image_folder}' does not exist!")
        return

    images = [img for img in os.listdir(image_folder) if img.endswith((".png", ".jpg", ".jpeg"))]
    images.sort()

    if not images:
        print(f"No frames found in '{image_folder}'!")
        return

    first_frame = cv2.imread(os.path.join(image_folder, images[0]))
    if first_frame is None:
        print("Error: Could not read the first frame.")
        return

    height, width, layers = first_frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    video = cv2.VideoWriter(video_name, fourcc, 20.0, (width, height))

    print(f"Reading frames from: {image_folder}")
    print(f"Stitching {len(images)} frames...")

    for image in images:
        frame_path = os.path.join(image_folder, image)
        frame = cv2.imread(frame_path)
        if frame is not None:
            video.write(frame)

    video.release()
    print(f"Done! Video saved as {video_name}")

if __name__ == "__main__":
    main()