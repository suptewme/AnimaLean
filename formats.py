LOTTIE_TEMPLATE = {
    "v": "5.7.4",
    "w": 128,
    "h": 128,
    "fr": 20,
    "layers": [],
    "assets": []
}

def build_lottie_json(frames_data, width, height, fps):
    return {
        "v": "5.7.4",
        "w": width,
        "h": height,
        "fr": fps,
        "layers": [
            {
                "ty": 2,
                "refId": f"image_{i}",
                "ks": {
                    "o": {"a": 0, "k": 100},
                    "r": {"a": 0, "k": 0},
                    "p": {"a": 0, "k": [width/2, height/2, 0]},
                    "a": {"a": 0, "k": [width/2, height/2, 0]},
                    "s": {"a": 0, "k": [100, 100, 100]}
                },
                "ip": i * (1/fps) * 100,
                "op": (i + 1) * (1/fps) * 100,
                "st": 0,
                "ind": i + 1
            } for i in range(len(frames_data))
        ],
        "assets": [
            {
                "id": f"image_{i}",
                "p": f"data:image/png;base64,{frame}"
            } for i, frame in enumerate(frames_data)
        ]
    }

def build_sprite_json(frames, cols, rows, width, height, delay):
    return {
        "type": "spritesheet",
        "image": "sprite.png",
        "columns": cols,
        "rows": rows,
        "frameWidth": width,
        "frameHeight": height,
        "totalFrames": len(frames),
        "delayMs": delay,
        "frames": [
            {
                "x": (i % cols) * width,
                "y": (i // cols) * height
            } for i in range(len(frames))
        ]
    }

def build_css_animation(frames, cols, rows, width, height, duration):
    css = f"""
.sprite-animation {{
    width: {width}px;
    height: {height}px;
    background-image: url('sprite.png');
    background-size: {cols * width}px {rows * height}px;
    animation: sprite-animation {duration}ms steps({len(frames)}) infinite;
}}
@keyframes sprite-animation {{
    from {{ background-position: 0 0; }}
    to {{ background-position: -{cols * width}px 0; }}
}}
"""
    return css

def build_android_xml(frames, delay):
    xml = '<?xml version="1.0" encoding="utf-8"?>\n<animation-list xmlns:android="http://schemas.android.com/apk/res/android">\n'
    for i in range(frames):
        xml += f'    <item android:drawable="@drawable/frame_{i}" android:duration="{delay}" />\n'
    xml += '</animation-list>'
    return xml

def build_swift_code(frames, width, height, delay):
    swift = f"""
import UIKit

class GiftAnimation: UIView {{
    private var imageView: UIImageView!
    private var images: [UIImage] = []
    private let duration: TimeInterval = {delay * len(frames) / 1000.0}
    
    override init(frame: CGRect) {{
        super.init(frame: frame)
        setupView()
        loadImages()
        animate()
    }}
    
    required init?(coder: NSCoder) {{
        fatalError("init(coder:) has not been implemented")
    }}
    
    private func setupView() {{
        imageView = UIImageView(frame: bounds)
        imageView.contentMode = .scaleAspectFit
        addSubview(imageView)
    }}
    
    private func loadImages() {{
        for i in 0..<{len(frames)} {{
            if let image = UIImage(named: "frame_\\(i)") {{
                images.append(image)
            }}
        }}
    }}
    
    private func animate() {{
        imageView.animationImages = images
        imageView.animationDuration = duration
        imageView.animationRepeatCount = 0
        imageView.startAnimating()
    }}
}}
"""
    return swift

def build_react_component(frames, width, height, delay):
    jsx = f"""
import React, {{ useState, useEffect, useRef }} from 'react';
import sprite from './sprite.png';

const GiftAnimation = () => {{
    const [frameIndex, setFrameIndex] = useState(0);
    const totalFrames = {len(frames)};
    const cols = {frames[0]['cols']};
    const frameWidth = {width};
    const frameHeight = {height};

    useEffect(() => {{
        const interval = setInterval(() => {{
            setFrameIndex((prev) => (prev + 1) % totalFrames);
        }}, {delay});
        return () => clearInterval(interval);
    }}, []);

    const style = {{
        width: frameWidth,
        height: frameHeight,
        backgroundImage: `url(${{sprite}})`,
        backgroundSize: `${{cols * frameWidth}}px auto`,
        backgroundPosition: `-${{(frameIndex % cols) * frameWidth}}px -${{Math.floor(frameIndex / cols) * frameHeight}}px`
    }};

    return <div style={{{
        width: frameWidth,
        height: frameHeight,
        overflow: 'hidden'
    }}}>
        <div style={{ style }} />
    </div>;
}};

export default GiftAnimation;
"""
    return jsx