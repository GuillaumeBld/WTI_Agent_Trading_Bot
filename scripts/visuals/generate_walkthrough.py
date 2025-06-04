"""
Video Walkthrough Generator

This script generates a video walkthrough of the trading system by capturing
screenshots and recording terminal output during a demonstration run.
"""

import os
import time
import subprocess
import argparse
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import cv2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../logs/walkthrough.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class WalkthroughGenerator:
    """
    Class to generate a video walkthrough of the trading system
    """
    
    def __init__(self, output_dir="../docs/walkthrough"):
        """
        Initialize the walkthrough generator
        
        Args:
            output_dir (str): Directory to save the walkthrough files
        """
        self.output_dir = output_dir
        self.screenshots_dir = os.path.join(output_dir, "screenshots")
        self.video_path = os.path.join(output_dir, f"walkthrough_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
        
        # Create directories if they don't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Initialize screenshot counter
        self.screenshot_count = 0
        
        # Initialize video writer
        self.video_writer = None
        
        # Initialize font for annotations
        try:
            # Try to load a font (this will depend on the system)
            self.font = ImageFont.truetype("Arial.ttf", 20)
        except IOError:
            # Fall back to default font
            self.font = ImageFont.load_default()
    
    def capture_screenshot(self, title, description):
        """
        Capture a screenshot of the terminal and annotate it
        
        Args:
            title (str): Title for the screenshot
            description (str): Description of what's happening
            
        Returns:
            str: Path to the saved screenshot
        """
        # Generate screenshot filename
        screenshot_path = os.path.join(self.screenshots_dir, f"screenshot_{self.screenshot_count:03d}.png")
        
        # Capture screenshot using system tools
        if os.name == 'posix':  # macOS or Linux
            subprocess.run(["screencapture", screenshot_path], check=True)
        elif os.name == 'nt':  # Windows
            import pyautogui
            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)
        
        # Annotate the screenshot
        img = Image.open(screenshot_path)
        draw = ImageDraw.Draw(img)
        
        # Add title and description
        draw.rectangle([(10, 10), (img.width - 10, 60)], fill=(0, 0, 0, 128))
        draw.text((20, 20), title, font=self.font, fill=(255, 255, 255))
        
        draw.rectangle([(10, img.height - 110), (img.width - 10, img.height - 10)], fill=(0, 0, 0, 128))
        draw.text((20, img.height - 100), description, font=self.font, fill=(255, 255, 255))
        
        # Save annotated screenshot
        img.save(screenshot_path)
        
        logger.info(f"Captured screenshot: {screenshot_path}")
        
        # Increment screenshot counter
        self.screenshot_count += 1
        
        return screenshot_path
    
    def start_video(self, width=1280, height=720, fps=1):
        """
        Start recording a video
        
        Args:
            width (int): Video width
            height (int): Video height
            fps (int): Frames per second
        """
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(self.video_path, fourcc, fps, (width, height))
        
        logger.info(f"Started video recording: {self.video_path}")
    
    def add_frame(self, image_path):
        """
        Add a frame to the video
        
        Args:
            image_path (str): Path to the image to add
        """
        if self.video_writer is None:
            logger.error("Video writer not initialized")
            return
        
        # Read image
        img = cv2.imread(image_path)
        
        # Resize image to match video dimensions
        img = cv2.resize(img, (self.video_writer.get(cv2.CAP_PROP_FRAME_WIDTH), self.video_writer.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        
        # Add frame to video
        self.video_writer.write(img)
    
    def finish_video(self):
        """
        Finish recording the video
        """
        if self.video_writer is None:
            logger.error("Video writer not initialized")
            return
        
        self.video_writer.release()
        logger.info(f"Finished video recording: {self.video_path}")
    
    def generate_walkthrough(self):
        """
        Generate a complete walkthrough of the trading system
        """
        logger.info("Generating walkthrough...")
        
        # Start video recording
        self.start_video()
        
        # Step 1: Introduction
        logger.info("Step 1: Introduction")
        time.sleep(1)  # Give time to switch to the terminal
        intro_text = """
        BTC Trading System Walkthrough
        
        This video demonstrates the key features and functionality of the
        BTC Trading System, including:
        
        1. Data acquisition
        2. Technical indicator calculation
        3. Machine learning model training
        4. Backtesting
        5. Trade signal generation
        6. Deployment
        
        Let's get started!
        """
        self.capture_screenshot("Introduction", intro_text)
        self.add_frame(os.path.join(self.screenshots_dir, f"screenshot_{self.screenshot_count-1:03d}.png"))
        
        # Step 2: Data Acquisition
        logger.info("Step 2: Data Acquisition")
        time.sleep(1)
        self.capture_screenshot("Data Acquisition", "Fetching historical data for BTC using Yahoo Finance API")
        self.add_frame(os.path.join(self.screenshots_dir, f"screenshot_{self.screenshot_count-1:03d}.png"))
        
        # Run data fetch script
        logger.info("Running data fetch script...")
        subprocess.run(["python", "../scripts/data_fetch.py"], check=True)
        
        self.capture_screenshot("Data Acquisition", "Data successfully fetched and saved to the data directory")
        self.add_frame(os.path.join(self.screenshots_dir, f"screenshot_{self.screenshot_count-1:03d}.png"))
        
        # Step 3: Technical Indicators
        logger.info("Step 3: Technical Indicators")
        time.sleep(1)
        self.capture_screenshot("Technical Indicators", "Calculating technical indicators (RSI, MACD, ADX, EMAs)")
        self.add_frame(os.path.join(self.screenshots_dir, f"screenshot_{self.screenshot_count-1:03d}.png"))
        
        # Generate a sample plot of indicators
        try:
            # Create a sample plot
            plt.figure(figsize=(10, 8))
            
            # Generate sample data
            dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
            prices = np.cumsum(np.random.randn(100)) + 100
            
            # Plot price
            plt.subplot(4, 1, 1)
            plt.plot(dates, prices)
            plt.title('BTC Price')
            plt.grid(True)
            
            # Plot RSI
            plt.subplot(4, 1, 2)
            rsi = np.random.uniform(30, 70, 100)
            plt.plot(dates, rsi)
            plt.axhline(y=70, color='r', linestyle='-')
            plt.axhline(y=30, color='g', linestyle='-')
            plt.title('RSI')
            plt.grid(True)
            
            # Plot MACD
            plt.subplot(4, 1, 3)
            macd = np.random.randn(100).cumsum()
            signal = np.random.randn(100).cumsum()
            plt.plot(dates, macd, label='MACD')
            plt.plot(dates, signal, label='Signal')
            plt.legend()
            plt.title('MACD')
            plt.grid(True)
            
            # Plot ADX
            plt.subplot(4, 1, 4)
            adx = np.random.uniform(10, 50, 100)
            plt.plot(dates, adx)
            plt.axhline(y=25, color='r', linestyle='-')
            plt.title('ADX')
            plt.grid(True)
            
            plt.tight_layout()
            
            # Save plot
            indicators_plot = os.path.join(self.screenshots_dir, "indicators_plot.png")
            plt.savefig(indicators_plot)
            plt.close()
            
            self.capture_screenshot("Technical Indicators", "Visualization of technical indicators")
            self.add_frame(os.path.join(self.screenshots_dir, f"screenshot_{self.screenshot_count-1:03d}.png"))
        except Exception as e:
            logger.error(f"Error generating indicators plot: {e}")
        
        # Step 4: Machine Learning Model
        logger.info("Step 4: Machine Learning Model")
        time.sleep(1)
        self.capture_screenshot("Machine Learning Model", "Training the LightGBM model for price prediction")
        self.add_frame(os.path.join(self.screenshots_dir, f"screenshot_{self.screenshot_count-1:03d}.png"))
        
        # Run strategy script with training
        logger.info("Running strategy script...")
        subprocess.run(["python", "../scripts/strategy.py", "--train"], check=True)
        
        self.capture_screenshot("Machine Learning Model", "Model trained and saved to the models directory")
        self.add_frame(os.path.join(self.screenshots_dir, f"screenshot_{self.screenshot_count-1:03d}.png"))
        
        # Step 5: Backtesting
        logger.info("Step 5: Backtesting")
        time.sleep(1)
        self.capture_screenshot("Backtesting", "Running backtest to evaluate strategy performance")
        self.add_frame(os.path.join(self.screenshots_dir, f"screenshot_{self.screenshot_count-1:03d}.png"))
        
        # Run backtest script
        logger.info("Running backtest script...")
        subprocess.run(["python", "../scripts/backtest.py", "--period", "1y", "--save"], check=True)
        
        self.capture_screenshot("Backtesting", "Backtest completed with performance metrics")
        self.add_frame(os.path.join(self.screenshots_dir, f"screenshot_{self.screenshot_count-1:03d}.png"))
        
        # Step 6: Trade Signal Generation
        logger.info("Step 6: Trade Signal Generation")
        time.sleep(1)
        self.capture_screenshot("Trade Signal Generation", "Generating trade signals based on model predictions")
        self.add_frame(os.path.join(self.screenshots_dir, f"screenshot_{self.screenshot_count-1:03d}.png"))
        
        # Run execute script (without Telegram)
        logger.info("Running execute script...")
        subprocess.run(["python", "../scripts/execute.py", "--once"], check=True)
        
        self.capture_screenshot("Trade Signal Generation", "Trade signal generated and ready for delivery")
        self.add_frame(os.path.join(self.screenshots_dir, f"screenshot_{self.screenshot_count-1:03d}.png"))
        
        # Step 7: Deployment
        logger.info("Step 7: Deployment")
        time.sleep(1)
        self.capture_screenshot("Deployment", "Deploying the trading system using Docker and cloud infrastructure")
        self.add_frame(os.path.join(self.screenshots_dir, f"screenshot_{self.screenshot_count-1:03d}.png"))
        
        # Show Docker and CI/CD files
        logger.info("Showing deployment files...")
        subprocess.run(["cat", "../Dockerfile"], check=True)
        time.sleep(2)
        
        self.capture_screenshot("Deployment", "Dockerfile for containerization")
        self.add_frame(os.path.join(self.screenshots_dir, f"screenshot_{self.screenshot_count-1:03d}.png"))
        
        subprocess.run(["cat", "../docker-compose.yml"], check=True)
        time.sleep(2)
        
        self.capture_screenshot("Deployment", "Docker Compose for orchestration")
        self.add_frame(os.path.join(self.screenshots_dir, f"screenshot_{self.screenshot_count-1:03d}.png"))
        
        # Step 8: Conclusion
        logger.info("Step 8: Conclusion")
        time.sleep(1)
        conclusion_text = """
        Conclusion

        This walkthrough demonstrated the key components of the BTC Trading System:
        
        1. Data acquisition from Yahoo Finance
        2. Technical indicator calculation (RSI, MACD, ADX, EMAs)
        3. Machine learning model training with LightGBM
        4. Backtesting to evaluate strategy performance
        5. Trade signal generation and delivery
        6. Deployment using Docker and cloud infrastructure
        
        The system is designed to be robust, scalable, and maintainable.
        
        For more information, please refer to the documentation:
        - README.md: Setup instructions
        - docs/trading_strategy.md: Detailed strategy documentation
        
        Thank you for watching!
        """
        self.capture_screenshot("Conclusion", conclusion_text)
        self.add_frame(os.path.join(self.screenshots_dir, f"screenshot_{self.screenshot_count-1:03d}.png"))
        
        # Finish video recording
        self.finish_video()
        
        logger.info(f"Walkthrough generated successfully: {self.video_path}")
        
        return self.video_path

def main():
    """
    Main function to generate a walkthrough
    """
    parser = argparse.ArgumentParser(description='Generate a video walkthrough of the trading system')
    parser.add_argument('--output-dir', type=str, default="../docs/walkthrough", help='Directory to save the walkthrough files')
    args = parser.parse_args()
    
    generator = WalkthroughGenerator(output_dir=args.output_dir)
    video_path = generator.generate_walkthrough()
    
    print(f"\nWalkthrough video generated: {video_path}")
    print("You can now share this video with stakeholders to demonstrate the system.")

if __name__ == "__main__":
    main()
