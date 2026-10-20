import os
import cv2
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def process_fruit(name):
    path = os.path.join(ASSETS_DIR, f"{name}.png")
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        print(f"Skipping {name}: not found")
        return
        
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Threshold dark background (< 18)
    fg_mask = (gray > 18).astype(np.uint8) * 255
    
    # Close any small gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    closed = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
    
    cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return
        
    # Get all contours that are part of the fruit (main body + stem/leaf)
    max_area = max(cv2.contourArea(c) for c in cnts)
    clean_mask = np.zeros((h, w), dtype=np.uint8)
    for c in cnts:
        if cv2.contourArea(c) >= max_area * 0.05:
            cv2.drawContours(clean_mask, [c], -1, 255, -1)
            
    # Crop tightly to the fruit with small padding
    x, y, bw, bh = cv2.boundingRect(clean_mask)
    pad = 4
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(w, x + bw + pad)
    y2 = min(h, y + bh + pad)
    
    crop_img = img[y1:y2, x1:x2]
    crop_mask = clean_mask[y1:y2, x1:x2]
    
    # Anti-alias the mask edges with gentle blur
    alpha = cv2.GaussianBlur(crop_mask, (3, 3), 0)
    # Inner region remains 100% solid
    eroded = cv2.erode(crop_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=1)
    alpha[eroded == 255] = 255
    
    b, g, r = cv2.split(crop_img)
    # Clear out any residual black color in transparent areas
    b[alpha == 0] = 0
    g[alpha == 0] = 0
    r[alpha == 0] = 0
    
    rgba = cv2.merge([b, g, r, alpha])
    cv2.imwrite(path, rgba)
    print(f"Successfully converted {name}.png to transparent RGBA: size {rgba.shape}")

def process_bomb():
    orig_bomb_path = r"C:\Users\farha\.gemini\antigravity\brain\0862d86d-afb3-48ca-a9c6-48b0e9fde6c7\bomb_1780430426801.png"
    if os.path.exists(orig_bomb_path):
        img = cv2.imread(orig_bomb_path, cv2.IMREAD_COLOR)
    else:
        img = cv2.imread(os.path.join(ASSETS_DIR, "bomb.png"), cv2.IMREAD_COLOR)
        
    if img is None:
        print("Bomb image not found")
        return
        
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Threshold dark background
    fg_mask = (gray > 14).astype(np.uint8) * 255
    
    # Morphological close to connect bomb body, wick rope, and flame
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    closed = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
    
    cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return
        
    # Get the main bomb contour
    c = max(cnts, key=cv2.contourArea)
    clean_mask = np.zeros((h, w), dtype=np.uint8)
    # Fill contour completely solid (ensures no dark holes inside bomb body)
    cv2.drawContours(clean_mask, [c], -1, 255, -1)
    
    # Crop tightly to the bomb
    x, y, bw, bh = cv2.boundingRect(c)
    pad = 6
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(w, x + bw + pad)
    y2 = min(h, y + bh + pad)
    
    crop_img = img[y1:y2, x1:x2]
    crop_mask = clean_mask[y1:y2, x1:x2]
    
    alpha = cv2.GaussianBlur(crop_mask, (3, 3), 0)
    eroded = cv2.erode(crop_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=1)
    alpha[eroded == 255] = 255
    
    b, g, r = cv2.split(crop_img)
    b[alpha == 0] = 0
    g[alpha == 0] = 0
    r[alpha == 0] = 0
    
    rgba = cv2.merge([b, g, r, alpha])
    out_path = os.path.join(ASSETS_DIR, "bomb.png")
    cv2.imwrite(out_path, rgba)
    print(f"Successfully converted bomb.png to transparent RGBA: size {rgba.shape}")

if __name__ == "__main__":
    for fruit in ["apple", "watermelon", "banana", "orange", "pineapple"]:
        process_fruit(fruit)
    process_bomb()
    print("All assets successfully processed with clear transparency!")
