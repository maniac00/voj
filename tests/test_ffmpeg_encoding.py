"""
FFmpeg 인코딩 서비스 테스트
"""
import sys
import os
import pytest
import tempfile
import shutil

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.encoding.ffmpeg_service import (
    FFmpegEncodingService,
    EncodingConfig,
    encode_audio_file,
    should_encode_file,
    get_encoding_preview
)

# 테스트 오디오 파일 경로
TEST_AUDIO_DIR = "/Users/kimsungwook/dev/voj/tmp_test_media/sample_audiobooks"


class TestFFmpegEncodingService:
    """FFmpeg 인코딩 서비스 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.service = FFmpegEncodingService()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """각 테스트 후 정리"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_ffmpeg_installation(self):
        """FFmpeg 설치 확인 테스트"""
        # 서비스 초기화 시 FFmpeg 검증이 이루어짐
        assert self.service.ffmpeg_path
        assert self.service.ffprobe_path
    
    def test_encoding_config_default(self):
        """기본 인코딩 설정 테스트"""
        config = EncodingConfig()
        
        assert config.output_format == "m4a"
        assert config.codec == "aac"
        assert config.bitrate == "56k"
        assert config.sample_rate == 44100
        assert config.channels == 1
        assert "-movflags" in config.additional_options
        assert "+faststart" in config.additional_options
    
    def test_encoding_config_custom(self):
        """커스텀 인코딩 설정 테스트"""
        config = EncodingConfig(
            bitrate="128k",
            channels=2,
            additional_options=["-metadata", "title=Test"]
        )
        
        assert config.bitrate == "128k"
        assert config.channels == 2
        assert "-metadata" in config.additional_options
    
    def test_build_ffmpeg_command(self):
        """FFmpeg 명령어 구성 테스트"""
        input_path = "/test/input.wav"
        output_path = "/test/output.m4a"
        
        cmd = self.service._build_ffmpeg_command(input_path, output_path)
        
        assert self.service.ffmpeg_path in cmd
        assert "-i" in cmd
        assert input_path in cmd
        assert output_path in cmd
        assert "-ac" in cmd
        assert "1" in cmd  # 모노
        assert "-ar" in cmd
        assert "44100" in cmd  # 샘플레이트
        assert "-c:a" in cmd
        assert "aac" in cmd
        assert "-b:a" in cmd
        assert "56k" in cmd

    @pytest.mark.skipif(
        not os.path.exists(TEST_AUDIO_DIR) or not os.listdir(TEST_AUDIO_DIR),
        reason="실제 오디오 파일이 없음"
    )
    def test_encode_real_mp3_file(self):
        """실제 MP3 파일 인코딩 테스트"""
        mp3_files = [f for f in os.listdir(TEST_AUDIO_DIR) if f.endswith('.mp3')]
        
        if not mp3_files:
            pytest.skip("MP3 파일이 없습니다")
        
        input_path = os.path.join(TEST_AUDIO_DIR, mp3_files[0])
        output_path = os.path.join(self.temp_dir, "encoded_output.m4a")
        
        print(f"Encoding: {mp3_files[0]}")
        print(f"Input size: {os.path.getsize(input_path) / (1024*1024):.2f} MB")
        
        # 인코딩 실행
        result = self.service.encode_audio(input_path, output_path)
        
        print(f"Encoding result: {result}")
        
        assert result.success
        assert result.output_path == output_path
        assert os.path.exists(output_path)
        assert result.metadata is not None
        assert result.encoded_size > 0
        assert result.processing_time > 0
        
        # 파일 크기 비교
        compression_ratio = result.original_size / result.encoded_size
        print(f"Compression ratio: {compression_ratio:.2f}x")
        print(f"Output size: {result.encoded_size / (1024*1024):.2f} MB")
        
        # AAC 56kbps 모노로 인코딩되었는지 확인
        assert result.metadata["format"] in ["aac", "m4a"]
        assert result.metadata["channels"] == 1
        assert result.metadata["sample_rate"] == 44100
        
        # 상당한 압축이 이루어졌는지 확인 (최소 2배)
        assert compression_ratio >= 2.0

    def test_encode_nonexistent_file(self):
        """존재하지 않는 파일 인코딩 테스트"""
        result = self.service.encode_audio("/nonexistent/file.wav")
        
        assert not result.success
        assert "not found" in result.error.lower()
    
    def test_encode_to_temp_file(self):
        """임시 파일로 인코딩 테스트"""
        mp3_files = [f for f in os.listdir(TEST_AUDIO_DIR) if f.endswith('.mp3')] if os.path.exists(TEST_AUDIO_DIR) else []
        
        if not mp3_files:
            pytest.skip("MP3 파일이 없습니다")
        
        input_path = os.path.join(TEST_AUDIO_DIR, mp3_files[0])
        
        success, temp_path, metadata = self.service.encode_to_temp_file(input_path)
        
        try:
            assert success
            assert os.path.exists(temp_path)
            assert metadata is not None
            assert metadata["channels"] == 1
            
        finally:
            # 임시 파일 정리
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_get_encoding_info(self):
        """인코딩 정보 조회 테스트"""
        mp3_files = [f for f in os.listdir(TEST_AUDIO_DIR) if f.endswith('.mp3')] if os.path.exists(TEST_AUDIO_DIR) else []
        
        if not mp3_files:
            pytest.skip("MP3 파일이 없습니다")
        
        input_path = os.path.join(TEST_AUDIO_DIR, mp3_files[0])
        
        info = self.service.get_encoding_info(input_path)
        
        print(f"Encoding info: {info}")
        
        assert "input_size" in info
        assert "input_duration" in info
        assert "estimated_output_size" in info
        assert "estimated_compression_ratio" in info
        assert "target_bitrate" in info
        
        assert info["target_bitrate"] == 56
        assert info["target_format"] == "m4a"
        assert info["target_channels"] == 1

    def test_should_encode_wav_file(self):
        """WAV 파일 인코딩 필요성 테스트"""
        # WAV 파일 시뮬레이션 (실제로는 존재하지 않아도 됨)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_wav.write(b"RIFF" + b"\x00" * 40 + b"WAVE" + b"\x00" * 1000)
            temp_wav_path = temp_wav.name
        
        try:
            # ffprobe 실패를 시뮬레이션하여 안전하게 인코딩 필요로 판단
            should_encode, reason = self.service.should_encode(temp_wav_path)
            
            assert should_encode
            assert "safety" in reason.lower() or "wav" in reason.lower()
            
        finally:
            os.unlink(temp_wav_path)

    @pytest.mark.skipif(
        not os.path.exists(TEST_AUDIO_DIR) or not os.listdir(TEST_AUDIO_DIR),
        reason="실제 오디오 파일이 없음"
    )
    def test_should_encode_mp3_file(self):
        """MP3 파일 인코딩 필요성 테스트"""
        mp3_files = [f for f in os.listdir(TEST_AUDIO_DIR) if f.endswith('.mp3')]
        
        if not mp3_files:
            pytest.skip("MP3 파일이 없습니다")
        
        input_path = os.path.join(TEST_AUDIO_DIR, mp3_files[0])
        
        should_encode, reason = self.service.should_encode(input_path)
        
        print(f"Should encode: {should_encode}, Reason: {reason}")
        
        # 192kbps 스테레오 MP3이므로 인코딩 필요로 판단되어야 함
        assert should_encode
        assert "bitrate" in reason.lower() or "channel" in reason.lower()


class TestEncodingIntegration:
    """인코딩 통합 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """각 테스트 후 정리"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.skipif(
        not os.path.exists(TEST_AUDIO_DIR) or not os.listdir(TEST_AUDIO_DIR),
        reason="실제 오디오 파일이 없음"
    )
    def test_complete_encoding_workflow(self):
        """완전한 인코딩 워크플로우 테스트"""
        mp3_files = [f for f in os.listdir(TEST_AUDIO_DIR) if f.endswith('.mp3')]
        
        if not mp3_files:
            pytest.skip("MP3 파일이 없습니다")
        
        input_path = os.path.join(TEST_AUDIO_DIR, mp3_files[0])
        output_path = os.path.join(self.temp_dir, "workflow_output.m4a")
        
        # 1. 인코딩 필요성 확인
        should_encode, reason = should_encode_file(input_path)
        print(f"Should encode: {should_encode} ({reason})")
        
        if should_encode:
            # 2. 인코딩 미리보기
            preview = get_encoding_preview(input_path)
            print(f"Encoding preview: {preview}")
            
            # 3. 실제 인코딩
            result = encode_audio_file(input_path, output_path)
            
            assert result.success
            assert os.path.exists(output_path)
            
            # 4. 결과 검증
            assert result.metadata["channels"] == 1
            assert result.metadata["sample_rate"] == 44100
            
            print(f"Encoding completed:")
            print(f"  Original: {result.original_size / (1024*1024):.2f} MB")
            print(f"  Encoded: {result.encoded_size / (1024*1024):.2f} MB")
            print(f"  Compression: {result.original_size / result.encoded_size:.2f}x")
            print(f"  Time: {result.processing_time:.2f}s")


# FFmpeg 설치 확인을 위한 스킵 조건
def pytest_configure(config):
    """pytest 설정"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, timeout=5)
        subprocess.run(["ffprobe", "-version"], capture_output=True, check=True, timeout=5)
    except:
        pytest.skip("FFmpeg not installed", allow_module_level=True)
