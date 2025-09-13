"""
FFmpeg 기반 오디오 인코딩 서비스
WAV → AAC (M4A) 변환 및 메타데이터 추출
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import json
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.utils.ffprobe import extract_audio_metadata


@dataclass
class EncodingConfig:
    """인코딩 설정"""
    output_format: str = "m4a"
    codec: str = "aac"
    bitrate: str = "56k"
    sample_rate: int = 44100
    channels: int = 1  # 모노
    additional_options: list[str] = None
    
    def __post_init__(self):
        if self.additional_options is None:
            self.additional_options = ["-movflags", "+faststart"]


@dataclass
class EncodingResult:
    """인코딩 결과"""
    success: bool
    output_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    original_size: int = 0
    encoded_size: int = 0
    processing_time: float = 0.0


class FFmpegEncodingService:
    """FFmpeg 인코딩 서비스"""
    
    def __init__(self, config: Optional[EncodingConfig] = None):
        self.config = config or EncodingConfig()
        self.ffmpeg_path = settings.FFMPEG_PATH
        self.ffprobe_path = settings.FFPROBE_PATH
        
        # FFmpeg 실행 파일 존재 확인
        self._validate_ffmpeg_installation()
    
    def _validate_ffmpeg_installation(self) -> None:
        """FFmpeg 설치 확인"""
        try:
            subprocess.run([self.ffmpeg_path, "-version"], 
                         capture_output=True, check=True, timeout=10)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            raise RuntimeError(f"FFmpeg not found or not working: {self.ffmpeg_path}")
        
        try:
            subprocess.run([self.ffprobe_path, "-version"], 
                         capture_output=True, check=True, timeout=10)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            raise RuntimeError(f"FFprobe not found or not working: {self.ffprobe_path}")
    
    def _build_ffmpeg_command(self, input_path: str, output_path: str) -> list[str]:
        """FFmpeg 명령어 구성"""
        cmd = [
            self.ffmpeg_path,
            "-y",  # 출력 파일 덮어쓰기
            "-i", input_path,  # 입력 파일
            "-ac", str(self.config.channels),  # 채널 수
            "-ar", str(self.config.sample_rate),  # 샘플레이트
            "-c:a", self.config.codec,  # 오디오 코덱
            "-b:a", self.config.bitrate,  # 비트레이트
        ]
        
        # 추가 옵션
        if self.config.additional_options:
            cmd.extend(self.config.additional_options)
        
        cmd.append(output_path)  # 출력 파일
        
        return cmd
    
    def encode_audio(self, input_path: str, output_path: Optional[str] = None) -> EncodingResult:
        """
        오디오 파일 인코딩
        
        Args:
            input_path: 입력 파일 경로
            output_path: 출력 파일 경로 (None이면 자동 생성)
        
        Returns:
            EncodingResult: 인코딩 결과
        """
        import time
        start_time = time.time()
        
        # 입력 파일 존재 확인
        if not os.path.exists(input_path):
            return EncodingResult(
                success=False,
                error=f"Input file not found: {input_path}"
            )
        
        original_size = os.path.getsize(input_path)
        
        # 출력 경로 설정
        if output_path is None:
            input_stem = Path(input_path).stem
            output_path = str(Path(input_path).parent / f"{input_stem}_encoded.{self.config.output_format}")
        
        try:
            # FFmpeg 명령어 실행
            cmd = self._build_ffmpeg_command(input_path, output_path)
            print(f"Running FFmpeg: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5분 타임아웃
                check=True
            )
            
            # 출력 파일 존재 확인
            if not os.path.exists(output_path):
                return EncodingResult(
                    success=False,
                    error="Encoding completed but output file not found"
                )
            
            encoded_size = os.path.getsize(output_path)
            processing_time = time.time() - start_time
            
            # 메타데이터 추출
            try:
                metadata = extract_audio_metadata(output_path)
            except Exception as meta_error:
                print(f"Metadata extraction warning: {meta_error}")
                metadata = {
                    "duration": 0,
                    "bitrate": int(self.config.bitrate.rstrip('k')),
                    "sample_rate": self.config.sample_rate,
                    "channels": self.config.channels,
                    "format": self.config.output_format
                }
            
            return EncodingResult(
                success=True,
                output_path=output_path,
                metadata=metadata,
                original_size=original_size,
                encoded_size=encoded_size,
                processing_time=processing_time
            )
            
        except subprocess.TimeoutExpired:
            return EncodingResult(
                success=False,
                error="Encoding timeout (exceeded 5 minutes)"
            )
        except subprocess.CalledProcessError as e:
            error_msg = f"FFmpeg failed: {e.stderr}" if e.stderr else f"FFmpeg exit code: {e.returncode}"
            return EncodingResult(
                success=False,
                error=error_msg
            )
        except Exception as e:
            return EncodingResult(
                success=False,
                error=f"Encoding failed: {str(e)}"
            )
    
    def encode_to_temp_file(self, input_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        임시 파일로 인코딩 (편의 메서드)
        
        Returns:
            (success, temp_output_path, metadata)
        """
        # 임시 출력 파일 생성
        with tempfile.NamedTemporaryFile(
            suffix=f".{self.config.output_format}", 
            delete=False
        ) as temp_file:
            temp_output_path = temp_file.name
        
        result = self.encode_audio(input_path, temp_output_path)
        
        if result.success:
            return True, temp_output_path, result.metadata
        else:
            # 실패 시 임시 파일 삭제
            if os.path.exists(temp_output_path):
                os.unlink(temp_output_path)
            return False, "", None
    
    def get_encoding_info(self, input_path: str) -> Dict[str, Any]:
        """
        인코딩 예상 정보 계산
        
        Args:
            input_path: 입력 파일 경로
            
        Returns:
            예상 출력 크기, 압축률 등 정보
        """
        try:
            # 입력 파일 메타데이터 추출
            input_metadata = extract_audio_metadata(input_path)
            input_size = os.path.getsize(input_path)
            
            # 예상 출력 크기 계산 (대략적)
            duration = input_metadata.get("duration", 0)
            target_bitrate = int(self.config.bitrate.rstrip('k'))  # kbps
            
            # 예상 크기 = (비트레이트 * 재생시간) / 8 (비트 → 바이트)
            estimated_size = (target_bitrate * 1000 * duration) // 8
            
            compression_ratio = input_size / estimated_size if estimated_size > 0 else 1
            
            return {
                "input_size": input_size,
                "input_duration": duration,
                "input_bitrate": input_metadata.get("bitrate"),
                "input_format": input_metadata.get("format"),
                "estimated_output_size": estimated_size,
                "estimated_compression_ratio": compression_ratio,
                "target_bitrate": target_bitrate,
                "target_format": self.config.output_format,
                "target_channels": self.config.channels,
                "target_sample_rate": self.config.sample_rate
            }
            
        except Exception as e:
            return {
                "error": f"Failed to analyze input file: {str(e)}"
            }
    
    def should_encode(self, input_path: str, force_encoding: bool = False) -> Tuple[bool, str]:
        """
        인코딩 필요 여부 판단
        
        Args:
            input_path: 입력 파일 경로
            force_encoding: 강제 인코딩 여부
            
        Returns:
            (should_encode, reason)
        """
        if force_encoding:
            return True, "Forced encoding requested"
        
        try:
            metadata = extract_audio_metadata(input_path)
            
            # 파일 형식 확인
            file_format = metadata.get("format", "").lower()
            if file_format in ["wav", "wave", "pcm"]:
                return True, "WAV format requires encoding"
            
            # 고품질 파일 확인 (비트레이트가 높거나 스테레오)
            bitrate = metadata.get("bitrate", 0)
            channels = metadata.get("channels", 1)
            
            if bitrate > 128:  # 128kbps 초과
                return True, f"High bitrate ({bitrate}kbps) - encoding for optimization"
            
            if channels > 1:
                return True, f"Multi-channel ({channels}ch) - encoding to mono"
            
            # 이미 최적화된 상태
            return False, f"Already optimized ({bitrate}kbps, {channels}ch)"
            
        except Exception as e:
            # 메타데이터 추출 실패 시 안전하게 인코딩
            return True, f"Metadata extraction failed - encoding for safety: {str(e)}"


# 전역 인코딩 서비스 인스턴스
encoding_service = FFmpegEncodingService()


def encode_audio_file(input_path: str, output_path: Optional[str] = None, 
                     config: Optional[EncodingConfig] = None) -> EncodingResult:
    """오디오 파일 인코딩 (편의 함수)"""
    service = FFmpegEncodingService(config) if config else encoding_service
    return service.encode_audio(input_path, output_path)


def should_encode_file(input_path: str, force: bool = False) -> Tuple[bool, str]:
    """인코딩 필요 여부 판단 (편의 함수)"""
    return encoding_service.should_encode(input_path, force)


def get_encoding_preview(input_path: str) -> Dict[str, Any]:
    """인코딩 미리보기 정보 (편의 함수)"""
    return encoding_service.get_encoding_info(input_path)
