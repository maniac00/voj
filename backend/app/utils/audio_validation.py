"""
오디오 파일 서버 사이드 검증 유틸리티
"""
from __future__ import annotations

import os
import mimetypes
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class AudioValidationResult:
    """오디오 검증 결과"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    file_info: Optional[Dict[str, Any]] = None


class AudioFileValidator:
    """오디오 파일 검증기"""
    
    # 지원되는 MIME 타입
    SUPPORTED_MIME_TYPES = {
        'audio/mpeg': ['.mp3'],
        'audio/wav': ['.wav'],
        'audio/wave': ['.wav'],
        'audio/x-wav': ['.wav'],
        'audio/mp4': ['.m4a', '.mp4'],
        'audio/x-m4a': ['.m4a'],
        'audio/flac': ['.flac'],
        'audio/x-flac': ['.flac'],
    }
    
    # 파일 시그니처 (매직 넘버)
    FILE_SIGNATURES = {
        b'\xFF\xFB': 'mp3',  # MP3 (MPEG-1 Layer 3)
        b'\xFF\xF3': 'mp3',  # MP3 (MPEG-2 Layer 3)
        b'\xFF\xF2': 'mp3',  # MP3 (MPEG-2.5 Layer 3)
        b'RIFF': 'wav',      # WAV (RIFF 헤더)
        b'fLaC': 'flac',     # FLAC
        b'\x00\x00\x00\x20ftypM4A': 'm4a',  # M4A
    }
    
    def __init__(self, 
                 max_file_size: int = 100 * 1024 * 1024,  # 100MB
                 min_duration: int = 5,  # 5초
                 max_duration: int = 4 * 60 * 60,  # 4시간
                 allowed_extensions: Optional[List[str]] = None):
        self.max_file_size = max_file_size
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.allowed_extensions = allowed_extensions or ['.mp3', '.wav', '.m4a', '.flac']
    
    def validate_file_basic(self, file_content: bytes, filename: str, content_type: str) -> AudioValidationResult:
        """기본 파일 검증"""
        errors = []
        warnings = []
        
        # 파일 크기 검증
        if len(file_content) > self.max_file_size:
            max_mb = self.max_file_size / (1024 * 1024)
            current_mb = len(file_content) / (1024 * 1024)
            errors.append(f"파일 크기 초과: {current_mb:.2f}MB > {max_mb:.0f}MB")
        
        if len(file_content) < 1024:  # 1KB 미만
            errors.append("파일이 너무 작습니다. 유효한 오디오 파일인지 확인해주세요.")
        
        # 파일 확장자 검증
        extension = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        if extension not in self.allowed_extensions:
            errors.append(f"지원되지 않는 파일 형식: {extension}")
        
        # MIME 타입 검증
        if content_type not in self.SUPPORTED_MIME_TYPES:
            errors.append(f"지원되지 않는 MIME 타입: {content_type}")
        
        # MIME 타입과 확장자 일치성 확인
        expected_extensions = self.SUPPORTED_MIME_TYPES.get(content_type, [])
        if extension not in expected_extensions:
            warnings.append(f"MIME 타입({content_type})과 파일 확장자({extension})가 일치하지 않습니다.")
        
        # 파일명 검증
        if not filename.strip():
            errors.append("파일명이 비어있습니다.")
        
        # 안전하지 않은 문자 검증
        unsafe_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        if any(char in filename for char in unsafe_chars):
            errors.append("파일명에 안전하지 않은 문자가 포함되어 있습니다.")
        
        return AudioValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_file_signature(self, file_content: bytes) -> AudioValidationResult:
        """파일 시그니처 검증"""
        errors = []
        warnings = []
        
        # 파일이 너무 작으면 시그니처 검증 건너뛰기
        if len(file_content) < 12:
            warnings.append("파일이 너무 작아 시그니처를 검증할 수 없습니다.")
            return AudioValidationResult(is_valid=True, errors=errors, warnings=warnings)
        
        # 시그니처 확인
        header = file_content[:12]
        signature_found = False
        
        for signature, format_name in self.FILE_SIGNATURES.items():
            if header.startswith(signature):
                signature_found = True
                break
            # WAV의 경우 RIFF...WAVE 패턴 확인
            if signature == b'RIFF' and len(header) >= 12:
                if header[8:12] == b'WAVE':
                    signature_found = True
                    break
        
        if not signature_found:
            # ID3 태그가 있는 MP3 파일 확인
            if header.startswith(b'ID3'):
                # ID3 태그 크기 계산하여 실제 오디오 데이터 위치 찾기
                if len(file_content) > 10:
                    tag_size = (header[6] << 21) | (header[7] << 14) | (header[8] << 7) | header[9]
                    audio_start = 10 + tag_size
                    
                    if len(file_content) > audio_start + 2:
                        audio_header = file_content[audio_start:audio_start + 2]
                        if audio_header[0] == 0xFF and (audio_header[1] & 0xE0) == 0xE0:
                            signature_found = True
            
            if not signature_found:
                errors.append("파일 시그니처가 올바르지 않습니다. 손상된 파일이거나 지원되지 않는 형식일 수 있습니다.")
        
        return AudioValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_audio_metadata(self, metadata: Dict[str, Any]) -> AudioValidationResult:
        """오디오 메타데이터 검증"""
        errors = []
        warnings = []
        
        duration = metadata.get('duration', 0)
        bitrate = metadata.get('bitrate', 0)
        sample_rate = metadata.get('sample_rate', 0)
        channels = metadata.get('channels', 0)
        
        # 재생시간 검증
        if duration < self.min_duration:
            errors.append(f"재생시간이 너무 짧습니다: {duration}초 < {self.min_duration}초")
        
        if duration > self.max_duration:
            max_hours = self.max_duration / 3600
            current_hours = duration / 3600
            errors.append(f"재생시간이 너무 깁니다: {current_hours:.1f}시간 > {max_hours:.1f}시간")
        
        # 비트레이트 검증
        if bitrate and (bitrate < 32 or bitrate > 320):
            if bitrate < 32:
                warnings.append(f"비트레이트가 낮습니다: {bitrate}kbps (권장: 64kbps 이상)")
            else:
                warnings.append(f"비트레이트가 높습니다: {bitrate}kbps (권장: 192kbps 이하)")
        
        # 샘플레이트 검증
        standard_rates = [8000, 11025, 16000, 22050, 44100, 48000]
        if sample_rate and sample_rate not in standard_rates:
            warnings.append(f"비표준 샘플레이트입니다: {sample_rate}Hz")
        
        # 채널 검증
        if channels > 2:
            warnings.append(f"다채널 오디오입니다: {channels}채널 (스테레오로 변환됩니다)")
        
        return AudioValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            file_info=metadata
        )
    
    def validate_filename_security(self, filename: str) -> AudioValidationResult:
        """파일명 보안 검증"""
        errors = []
        warnings = []
        
        # 경로 순회 공격 방지
        if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
            errors.append("안전하지 않은 파일명입니다.")
        
        # 시스템 파일명 방지
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        
        name_without_ext = filename.rsplit('.', 1)[0].upper()
        if name_without_ext in reserved_names:
            errors.append("시스템 예약어는 파일명으로 사용할 수 없습니다.")
        
        # 길이 제한
        if len(filename.encode('utf-8')) > 255:
            errors.append("파일명이 너무 깁니다. (UTF-8 기준 255바이트 초과)")
        
        # 제어 문자 확인
        if any(ord(char) < 32 for char in filename):
            errors.append("파일명에 제어 문자가 포함되어 있습니다.")
        
        return AudioValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_complete(self, 
                         file_content: bytes, 
                         filename: str, 
                         content_type: str,
                         metadata: Optional[Dict[str, Any]] = None) -> AudioValidationResult:
        """종합적인 검증"""
        all_errors = []
        all_warnings = []
        
        # 1. 기본 검증
        basic_result = self.validate_file_basic(file_content, filename, content_type)
        all_errors.extend(basic_result.errors)
        all_warnings.extend(basic_result.warnings)
        
        # 2. 파일명 보안 검증
        security_result = self.validate_filename_security(filename)
        all_errors.extend(security_result.errors)
        all_warnings.extend(security_result.warnings)
        
        # 3. 파일 시그니처 검증
        signature_result = self.validate_file_signature(file_content)
        all_errors.extend(signature_result.errors)
        all_warnings.extend(signature_result.warnings)
        
        # 4. 메타데이터 검증 (있는 경우)
        file_info = None
        if metadata:
            metadata_result = self.validate_audio_metadata(metadata)
            all_errors.extend(metadata_result.errors)
            all_warnings.extend(metadata_result.warnings)
            file_info = metadata_result.file_info
        
        return AudioValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            file_info=file_info
        )


# 전역 검증기 인스턴스
audio_validator = AudioFileValidator()


def validate_uploaded_audio(file_content: bytes, 
                           filename: str, 
                           content_type: str,
                           metadata: Optional[Dict[str, Any]] = None) -> AudioValidationResult:
    """업로드된 오디오 파일 검증 (편의 함수)"""
    return audio_validator.validate_complete(file_content, filename, content_type, metadata)


def get_audio_file_info(filename: str, content_type: str) -> Dict[str, str]:
    """오디오 파일 기본 정보 추출"""
    extension = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
    
    format_info = {
        '.mp3': {'format': 'MP3', 'codec': 'MPEG Audio Layer 3'},
        '.wav': {'format': 'WAV', 'codec': 'PCM'},
        '.m4a': {'format': 'M4A', 'codec': 'AAC'},
        '.flac': {'format': 'FLAC', 'codec': 'FLAC Lossless'},
    }
    
    info = format_info.get(extension, {'format': 'Unknown', 'codec': 'Unknown'})
    
    return {
        'extension': extension,
        'mime_type': content_type,
        'format_name': info['format'],
        'codec_name': info['codec']
    }


def sanitize_filename(filename: str) -> str:
    """파일명 정리 (안전한 문자만 유지)"""
    import re
    
    # 기본 정리
    sanitized = filename.strip()
    
    # 안전하지 않은 문자 제거
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', sanitized)
    
    # 연속된 공백을 하나로
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # 연속된 언더스코어를 하나로
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # 앞뒤 점과 공백 제거
    sanitized = sanitized.strip('. ')
    
    # 빈 파일명 처리
    if not sanitized:
        sanitized = 'unnamed_audio'
    
    return sanitized


def extract_chapter_info(filename: str) -> Dict[str, Any]:
    """파일명에서 챕터 정보 추출"""
    import re
    
    sanitized_name = sanitize_filename(filename)
    name_without_ext = sanitized_name.rsplit('.', 1)[0]
    
    # 챕터 번호 패턴 매칭
    chapter_patterns = [
        (r'(\d+)_(\d+)', lambda m: int(m.group(2))),  # "1_1" → 1
        (r'chapter\s*(\d+)', lambda m: int(m.group(1))),  # "Chapter 1" → 1
        (r'(\d+)장', lambda m: int(m.group(1))),  # "1장" → 1
        (r'(\d+)편', lambda m: int(m.group(1))),  # "1편" → 1
        (r'(\d+)회', lambda m: int(m.group(1))),  # "1회" → 1
        (r'^(\d+)', lambda m: int(m.group(1))),  # 시작 숫자 → 숫자
    ]
    
    chapter_number = None
    suggested_title = name_without_ext
    
    for pattern, extractor in chapter_patterns:
        match = re.search(pattern, name_without_ext, re.IGNORECASE)
        if match:
            try:
                chapter_number = extractor(match)
                # 패턴 부분을 제거하여 제목 추출
                suggested_title = re.sub(pattern, '', name_without_ext, flags=re.IGNORECASE).strip()
                break
            except (ValueError, IndexError):
                continue
    
    # 빈 제목 처리
    if not suggested_title or suggested_title in ['_', '-']:
        suggested_title = f"Chapter {chapter_number}" if chapter_number else "Untitled"
    
    return {
        'original_filename': filename,
        'sanitized_filename': sanitized_name,
        'suggested_title': suggested_title,
        'chapter_number': chapter_number
    }


def validate_chapter_sequence(chapters: List[Dict[str, Any]]) -> List[str]:
    """챕터 시퀀스 검증"""
    warnings = []
    
    if not chapters:
        return warnings
    
    # 챕터 번호가 있는 것들만 확인
    numbered_chapters = [c for c in chapters if c.get('chapter_number')]
    
    if len(numbered_chapters) < 2:
        return warnings
    
    # 정렬
    numbered_chapters.sort(key=lambda x: x['chapter_number'])
    
    # 연속성 확인
    for i in range(1, len(numbered_chapters)):
        prev_num = numbered_chapters[i-1]['chapter_number']
        curr_num = numbered_chapters[i]['chapter_number']
        
        if curr_num - prev_num > 1:
            warnings.append(f"챕터 번호 누락: {prev_num} 다음에 {curr_num}")
        elif curr_num == prev_num:
            warnings.append(f"중복된 챕터 번호: {curr_num}")
    
    return warnings
