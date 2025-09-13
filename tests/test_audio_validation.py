"""
오디오 파일 검증 시스템 테스트
"""
import sys
import os
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.utils.audio_validation import (
    AudioFileValidator,
    validate_uploaded_audio,
    extract_chapter_info,
    sanitize_filename,
    validate_chapter_sequence
)


class TestAudioFileValidator:
    """오디오 파일 검증기 테스트"""
    
    def setup_method(self):
        self.validator = AudioFileValidator()
    
    def test_validate_file_basic_success(self):
        """기본 파일 검증 성공 테스트"""
        # 유효한 MP3 헤더 시뮬레이션
        mp3_content = b'\xFF\xFB' + b'\x00' * 10000  # MP3 시그니처 + 충분한 크기 (10KB)
        
        result = self.validator.validate_file_basic(mp3_content, "test.mp3", "audio/mpeg")
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_file_basic_too_large(self):
        """파일 크기 초과 테스트"""
        large_content = b'\xFF\xFB' + b'\x00' * (101 * 1024 * 1024)  # 101MB
        
        result = self.validator.validate_file_basic(large_content, "large.mp3", "audio/mpeg")
        
        assert not result.is_valid
        assert any("크기 초과" in error for error in result.errors)
    
    def test_validate_file_basic_invalid_extension(self):
        """잘못된 확장자 테스트"""
        content = b'\xFF\xFB' + b'\x00' * 1000
        
        result = self.validator.validate_file_basic(content, "test.txt", "audio/mpeg")
        
        assert not result.is_valid
        assert any("지원되지 않는 파일 형식" in error for error in result.errors)
    
    def test_validate_file_signature_mp3(self):
        """MP3 파일 시그니처 검증 테스트"""
        mp3_content = b'\xFF\xFB' + b'\x00' * 100
        
        result = self.validator.validate_file_signature(mp3_content)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_file_signature_wav(self):
        """WAV 파일 시그니처 검증 테스트"""
        wav_content = b'RIFF\x00\x00\x00\x00WAVE' + b'\x00' * 100
        
        result = self.validator.validate_file_signature(wav_content)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_file_signature_invalid(self):
        """잘못된 파일 시그니처 테스트"""
        invalid_content = b'INVALID_HEADER' + b'\x00' * 100
        
        result = self.validator.validate_file_signature(invalid_content)
        
        assert not result.is_valid
        assert any("시그니처" in error for error in result.errors)
    
    def test_validate_audio_metadata_success(self):
        """오디오 메타데이터 검증 성공 테스트"""
        metadata = {
            'duration': 300,  # 5분
            'bitrate': 128,   # 128kbps
            'sample_rate': 44100,
            'channels': 2
        }
        
        result = self.validator.validate_audio_metadata(metadata)
        
        assert result.is_valid
        assert result.file_info == metadata
    
    def test_validate_audio_metadata_too_short(self):
        """재생시간 너무 짧은 경우 테스트"""
        metadata = {
            'duration': 2,  # 2초 (최소 5초 미만)
            'bitrate': 128,
            'sample_rate': 44100,
            'channels': 2
        }
        
        result = self.validator.validate_audio_metadata(metadata)
        
        assert not result.is_valid
        assert any("너무 짧습니다" in error for error in result.errors)
    
    def test_validate_audio_metadata_high_bitrate_warning(self):
        """높은 비트레이트 경고 테스트"""
        metadata = {
            'duration': 300,
            'bitrate': 500,  # 320kbps 초과
            'sample_rate': 44100,
            'channels': 2
        }
        
        result = self.validator.validate_audio_metadata(metadata)
        
        assert result.is_valid  # 경고이므로 유효함
        assert any("높습니다" in warning for warning in result.warnings)


class TestChapterInfoExtraction:
    """챕터 정보 추출 테스트"""
    
    def test_extract_chapter_info_numbered(self):
        """번호가 있는 파일명 테스트"""
        filename = "나의 아버지 순교자 주기철 목사 2_2.mp3"
        
        result = extract_chapter_info(filename)
        
        assert result['chapter_number'] == 2
        assert result['suggested_title'] == "나의 아버지 순교자 주기철 목사"
        assert result['sanitized_filename'] == filename
    
    def test_extract_chapter_info_chapter_format(self):
        """Chapter 형식 파일명 테스트"""
        filename = "Chapter 3 - Introduction.mp3"
        
        result = extract_chapter_info(filename)
        
        assert result['chapter_number'] == 3
        assert "Introduction" in result['suggested_title']
    
    def test_extract_chapter_info_korean(self):
        """한글 챕터 형식 테스트"""
        filename = "5장 새로운 시작.mp3"
        
        result = extract_chapter_info(filename)
        
        assert result['chapter_number'] == 5
        assert "새로운 시작" in result['suggested_title']
    
    def test_sanitize_filename_unsafe_chars(self):
        """안전하지 않은 문자 정리 테스트"""
        unsafe_filename = 'test<>:"/\\|?*file.mp3'
        
        result = sanitize_filename(unsafe_filename)
        
        assert '<' not in result
        assert '>' not in result
        assert ':' not in result
        assert '"' not in result
        assert '\\' not in result
        assert '|' not in result
        assert '?' not in result
        assert '*' not in result
    
    def test_sanitize_filename_multiple_spaces(self):
        """연속된 공백 정리 테스트"""
        filename = "test    multiple   spaces.mp3"
        
        result = sanitize_filename(filename)
        
        assert "    " not in result
        assert "   " not in result
        assert "  " not in result


class TestChapterSequenceValidation:
    """챕터 시퀀스 검증 테스트"""
    
    def test_validate_chapter_sequence_continuous(self):
        """연속된 챕터 번호 테스트"""
        chapters = [
            {'chapter_number': 1, 'title': 'Chapter 1'},
            {'chapter_number': 2, 'title': 'Chapter 2'},
            {'chapter_number': 3, 'title': 'Chapter 3'},
        ]
        
        warnings = validate_chapter_sequence(chapters)
        
        assert len(warnings) == 0
    
    def test_validate_chapter_sequence_gap(self):
        """챕터 번호 누락 테스트"""
        chapters = [
            {'chapter_number': 1, 'title': 'Chapter 1'},
            {'chapter_number': 3, 'title': 'Chapter 3'},  # 2번 누락
            {'chapter_number': 4, 'title': 'Chapter 4'},
        ]
        
        warnings = validate_chapter_sequence(chapters)
        
        assert len(warnings) > 0
        assert any("누락" in warning for warning in warnings)
    
    def test_validate_chapter_sequence_duplicate(self):
        """중복 챕터 번호 테스트"""
        chapters = [
            {'chapter_number': 1, 'title': 'Chapter 1'},
            {'chapter_number': 2, 'title': 'Chapter 2a'},
            {'chapter_number': 2, 'title': 'Chapter 2b'},  # 중복
        ]
        
        warnings = validate_chapter_sequence(chapters)
        
        assert len(warnings) > 0
        assert any("중복" in warning for warning in warnings)


class TestIntegrationValidation:
    """통합 검증 테스트"""
    
    def test_validate_uploaded_audio_success(self):
        """업로드된 오디오 종합 검증 성공 테스트"""
        mp3_content = b'\xFF\xFB' + b'\x00' * 10000  # 유효한 MP3 시뮬레이션
        filename = "test_chapter.mp3"
        content_type = "audio/mpeg"
        
        metadata = {
            'duration': 120,
            'bitrate': 128,
            'sample_rate': 44100,
            'channels': 2,
            'format': 'mp3'
        }
        
        result = validate_uploaded_audio(mp3_content, filename, content_type, metadata)
        
        assert result.is_valid
        assert result.file_info == metadata
    
    def test_validate_uploaded_audio_multiple_errors(self):
        """여러 검증 오류 테스트"""
        # 너무 작고, 잘못된 시그니처, 잘못된 메타데이터
        invalid_content = b'INVALID'  # 너무 작고 잘못된 시그니처
        filename = "test<>.mp3"  # 안전하지 않은 문자
        content_type = "audio/mpeg"
        
        metadata = {
            'duration': 2,  # 너무 짧음
            'bitrate': 10,  # 너무 낮음
            'sample_rate': 8000,
            'channels': 1
        }
        
        result = validate_uploaded_audio(invalid_content, filename, content_type, metadata)
        
        assert not result.is_valid
        assert len(result.errors) > 1  # 여러 오류가 있어야 함
        
        # 구체적인 오류 확인
        error_text = ' '.join(result.errors)
        assert "작습니다" in error_text
        assert "시그니처" in error_text or "안전하지 않은" in error_text
        assert "짧습니다" in error_text


@pytest.mark.skipif(
    not os.path.exists("/Users/kimsungwook/dev/voj/tmp_test_media/sample_audiobooks"),
    reason="실제 오디오 파일이 없음"
)
class TestRealFileValidation:
    """실제 파일 검증 테스트"""
    
    def test_validate_real_mp3_file(self):
        """실제 MP3 파일 검증 테스트"""
        test_dir = "/Users/kimsungwook/dev/voj/tmp_test_media/sample_audiobooks"
        mp3_files = [f for f in os.listdir(test_dir) if f.endswith('.mp3')]
        
        if not mp3_files:
            pytest.skip("MP3 파일이 없습니다")
        
        test_file_path = os.path.join(test_dir, mp3_files[0])
        
        with open(test_file_path, 'rb') as f:
            file_content = f.read()
        
        # 메타데이터 추출
        from app.utils.ffprobe import extract_audio_metadata
        metadata = extract_audio_metadata(test_file_path)
        
        # 종합 검증
        result = validate_uploaded_audio(
            file_content=file_content,
            filename=mp3_files[0],
            content_type="audio/mpeg",
            metadata=metadata
        )
        
        print(f"Validation result for {mp3_files[0]}:")
        print(f"  Valid: {result.is_valid}")
        print(f"  Errors: {result.errors}")
        print(f"  Warnings: {result.warnings}")
        print(f"  Metadata: {result.file_info}")
        
        assert result.is_valid  # 실제 파일이므로 유효해야 함
        
        # 챕터 정보 추출 테스트
        chapter_info = extract_chapter_info(mp3_files[0])
        print(f"Chapter info: {chapter_info}")
        
        assert 'suggested_title' in chapter_info
        assert 'sanitized_filename' in chapter_info
