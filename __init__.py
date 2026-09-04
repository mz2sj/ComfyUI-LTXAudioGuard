import torch
from comfy_api.latest import InputImpl, Types


class LTXSourceAudioGuard:
    """
    有源音频：原样输出。
    无源音频：根据 frame_count / fps 自动生成等长静音，
    只用于保证 LTX 的音频 latent 链可以正常运行。
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "frame_count": (
                    "INT",
                    {
                        "default": 121,
                        "min": 1,
                        "max": 100000,
                    },
                ),
                "fps": (
                    "FLOAT",
                    {
                        "default": 24.0,
                        "min": 0.01,
                        "max": 1000.0,
                        "step": 0.01,
                    },
                ),
                "sample_rate": (
                    "INT",
                    {
                        "default": 48000,
                        "min": 8000,
                        "max": 192000,
                    },
                ),
                "channels": (
                    "INT",
                    {
                        "default": 2,
                        "min": 1,
                        "max": 2,
                    },
                ),
            },
            "optional": {
                "audio": ("AUDIO",),
            },
        }

    RETURN_TYPES = (
        "AUDIO",
        "AUDIO",
        "BOOLEAN",
    )

    RETURN_NAMES = (
        "audio_for_ltx",
        "original_audio",
        "has_audio",
    )

    FUNCTION = "run"
    CATEGORY = "LTX/audio"

    def run(
        self,
        frame_count,
        fps,
        sample_rate,
        channels,
        audio=None,
    ):
        # 有真实音轨：完全原样通过
        if audio is not None:
            return (
                audio,
                audio,
                True,
            )

        # 无真实音轨：按视频实际时长创建静音
        fps = max(float(fps), 0.01)
        duration = float(frame_count) / fps

        samples = max(
            1,
            int(round(duration * int(sample_rate))),
        )

        waveform = torch.zeros(
            (
                1,
                int(channels),
                samples,
            ),
            dtype=torch.float32,
        )

        silent_audio = {
            "waveform": waveform,
            "sample_rate": int(sample_rate),
        }

        # 第二路保留 None：
        # 最后输出视频不会因为兜底静音而被强制添加音轨
        return (
            silent_audio,
            None,
            False,
        )


class LTXRestoreSourceAudio:
    """
    使用生成视频的画面/FPS/bit depth，
    将源视频原音频重新挂回最终 VIDEO。

    source_audio = None 时，最终 VIDEO 不带音频。
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "generated_video": ("VIDEO",),
            },
            "optional": {
                "source_audio": ("AUDIO",),
            },
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)

    FUNCTION = "run"
    CATEGORY = "LTX/audio"

    def run(
        self,
        generated_video,
        source_audio=None,
    ):
        components = generated_video.get_components()

        output_video = InputImpl.VideoFromComponents(
            Types.VideoComponents(
                images=components.images,
                audio=source_audio,
                frame_rate=components.frame_rate,
            ),
            bit_depth=generated_video.get_bit_depth(),
        )

        return (output_video,)


NODE_CLASS_MAPPINGS = {
    "LTXSourceAudioGuard": LTXSourceAudioGuard,
    "LTXRestoreSourceAudio": LTXRestoreSourceAudio,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LTXSourceAudioGuard":
        "LTX Source Audio Guard (Auto Silence)",

    "LTXRestoreSourceAudio":
        "LTX Restore Source Audio",
}
