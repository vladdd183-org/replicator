#!/usr/bin/env python3
"""
Тестовый скрипт для Streaming WebSocket API

Использование:
    python test_streaming_websocket.py image.jpg
    python test_streaming_websocket.py image.jpg --mode regions --regions regions.json
    python test_streaming_websocket.py image.jpg --from-lang zh --to-lang ru
    
Примечание: количество воркеров зафиксировано (OCR=1, Translation=2)
"""

import asyncio
import websockets
import json
import argparse
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import sys


# Цвета для красивого вывода
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_colored(text: str, color: str = Colors.ENDC):
    """Вывод цветного текста."""
    print(f"{color}{text}{Colors.ENDC}")


def print_section(title: str):
    """Вывод заголовка секции."""
    print("\n" + "="*60)
    print_colored(f"  {title}", Colors.BOLD + Colors.CYAN)
    print("="*60)


class StreamingWebSocketTester:
    """Тестер для Streaming WebSocket API."""
    
    def __init__(
        self, 
        url: str,
        image_path: Path,
        from_lang: str = "zh",
        to_lang: str = "ru",
        mode: str = "image"
    ):
        self.url = url
        self.image_path = image_path
        self.from_lang = from_lang
        self.to_lang = to_lang
        self.mode = mode
        
        # Метрики
        self.start_time = None
        self.first_result_time = None
        self.regions_count = 0
        self.ocr_completed = 0
        self.translations_completed = 0
        self.errors_count = 0
    
    async def test_process_image_streaming(self):
        """Тест потоковой обработки полного изображения."""
        
        print_section("🚀 STREAMING WEBSOCKET TEST - FULL IMAGE")
        print_colored(f"📁 Image: {self.image_path}", Colors.BLUE)
        print_colored(f"🔗 URL: {self.url}", Colors.BLUE)
        print_colored(f"⚙️  Workers: OCR=1 (fixed), Translation=2 (fixed)", Colors.BLUE)
        print_colored(f"🌍 Languages: {self.from_lang} → {self.to_lang}", Colors.BLUE)
        
        try:
            # Теперь ping/pong работает т.к. OCR выполняется в отдельных потоках
            async with websockets.connect(
                self.url,
                ping_interval=20,    # Ping каждые 20 секунд
                ping_timeout=10,     # Ожидание pong 10 секунд
                close_timeout=10,    # Таймаут для закрытия соединения
                max_size=10 * 1024 * 1024  # Максимальный размер сообщения 10MB
            ) as websocket:
                print_colored("\n✅ WebSocket connection established", Colors.GREEN)
                
                # 1. Отправляем метаданные
                print_section("📤 Step 1: Sending metadata")
                
                image_size = self.image_path.stat().st_size
                metadata = {
                    "action": "process_image_streaming",
                    "filename": self.image_path.name,
                    "size": image_size,
                    "from_language": self.from_lang,
                    "to_language": self.to_lang,
                    "min_confidence_threshold": 0.1,
                    "translate_empty_results": False,
                    "streaming_config": {
                        "send_region_preview": True
                    }
                }
                
                print(json.dumps(metadata, indent=2, ensure_ascii=False))
                await websocket.send(json.dumps(metadata))
                
                # 2. Ждём подтверждение
                response = json.loads(await websocket.recv())
                print_colored(f"\n📩 Server response: {response.get('status')}", Colors.CYAN)
                print_colored(f"   {response.get('message')}", Colors.CYAN)
                
                if response.get('status') != 'ready':
                    print_colored(f"❌ Error: {response.get('message')}", Colors.RED)
                    return
                
                # 3. Отправляем изображение
                print_section("📤 Step 2: Sending image data")
                
                with open(self.image_path, 'rb') as f:
                    image_data = f.read()
                
                print_colored(f"📊 Image size: {len(image_data):,} bytes", Colors.BLUE)
                await websocket.send(image_data)
                print_colored("✅ Image sent successfully", Colors.GREEN)
                
                # 4. Получаем поток событий
                print_section("📥 Step 3: Receiving streaming events")
                
                self.start_time = time.time()
                
                while True:
                    try:
                        message_raw = await websocket.recv()
                        
                        # Проверяем тип сообщения
                        if isinstance(message_raw, bytes):
                            print_colored(f"\n⚠️  Received binary message ({len(message_raw)} bytes), skipping", Colors.YELLOW)
                            continue
                        
                        message = json.loads(message_raw)
                        
                        await self._handle_message(message)
                        
                        # Проверяем завершение
                        if message.get('type') == 'completed':
                            break
                        elif message.get('status') == 'error':
                            print_colored(f"\n❌ Error: {message.get('message')}", Colors.RED)
                            break
                    
                    except websockets.exceptions.ConnectionClosed as e:
                        print_colored(f"\n⚠️  WebSocket connection closed: {e}", Colors.YELLOW)
                        break
                    except json.JSONDecodeError as e:
                        print_colored(f"\n⚠️  Failed to parse JSON: {e}", Colors.YELLOW)
                        print_colored(f"   Raw message: {message_raw[:200]}...", Colors.YELLOW)
                        continue
                    except Exception as e:
                        print_colored(f"\n❌ Unexpected error: {e}", Colors.RED)
                        import traceback
                        traceback.print_exc()
                        break
                
                # 5. Итоговые метрики
                self._print_summary()
        
        except Exception as e:
            print_colored(f"\n❌ Connection error: {e}", Colors.RED)
            import traceback
            traceback.print_exc()
    
    async def test_process_regions_streaming(self, regions: list):
        """Тест потоковой обработки заданных областей."""
        
        print_section("🚀 STREAMING WEBSOCKET TEST - REGIONS")
        print_colored(f"📁 Image: {self.image_path}", Colors.BLUE)
        print_colored(f"🔗 URL: {self.url}", Colors.BLUE)
        print_colored(f"📍 Regions: {len(regions)}", Colors.BLUE)
        print_colored(f"⚙️  Workers: OCR=1 (fixed), Translation=2 (fixed)", Colors.BLUE)
        
        try:
            # Теперь ping/pong работает т.к. OCR выполняется в отдельных потоках
            async with websockets.connect(
                self.url,
                ping_interval=20,    # Ping каждые 20 секунд
                ping_timeout=10,     # Ожидание pong 10 секунд
                close_timeout=10,    # Таймаут для закрытия соединения
                max_size=10 * 1024 * 1024  # Максимальный размер сообщения 10MB
            ) as websocket:
                print_colored("\n✅ WebSocket connection established", Colors.GREEN)
                
                # 1. Отправляем метаданные с регионами
                print_section("📤 Step 1: Sending metadata with regions")
                
                image_size = self.image_path.stat().st_size
                metadata = {
                    "action": "process_regions_streaming",
                    "filename": self.image_path.name,
                    "size": image_size,
                    "regions": regions,
                    "from_language": self.from_lang,
                    "to_language": self.to_lang,
                    "min_confidence_threshold": 0.1,
                    "translate_empty_results": False,
                    "streaming_config": {
                        "send_region_preview": True
                    }
                }
                
                print(json.dumps(metadata, indent=2, ensure_ascii=False))
                await websocket.send(json.dumps(metadata))
                
                # 2. Ждём подтверждение
                response = json.loads(await websocket.recv())
                print_colored(f"\n📩 Server response: {response.get('status')}", Colors.CYAN)
                
                if response.get('status') != 'ready':
                    print_colored(f"❌ Error: {response.get('message')}", Colors.RED)
                    return
                
                # 3. Отправляем изображение
                print_section("📤 Step 2: Sending image data")
                
                with open(self.image_path, 'rb') as f:
                    image_data = f.read()
                
                await websocket.send(image_data)
                print_colored("✅ Image sent successfully", Colors.GREEN)
                
                # 4. Получаем поток событий
                print_section("📥 Step 3: Receiving streaming events")
                
                self.start_time = time.time()
                
                while True:
                    try:
                        message_raw = await websocket.recv()
                        
                        # Проверяем тип сообщения
                        if isinstance(message_raw, bytes):
                            print_colored(f"\n⚠️  Received binary message ({len(message_raw)} bytes), skipping", Colors.YELLOW)
                            continue
                        
                        message = json.loads(message_raw)
                        
                        await self._handle_message(message)
                        
                        if message.get('type') == 'completed':
                            break
                        elif message.get('status') == 'error':
                            print_colored(f"\n❌ Error: {message.get('message')}", Colors.RED)
                            break
                    
                    except websockets.exceptions.ConnectionClosed as e:
                        print_colored(f"\n⚠️  WebSocket connection closed: {e}", Colors.YELLOW)
                        break
                    except json.JSONDecodeError as e:
                        print_colored(f"\n⚠️  Failed to parse JSON: {e}", Colors.YELLOW)
                        print_colored(f"   Raw message: {message_raw[:200]}...", Colors.YELLOW)
                        continue
                    except Exception as e:
                        print_colored(f"\n❌ Unexpected error: {e}", Colors.RED)
                        import traceback
                        traceback.print_exc()
                        break
                
                # 5. Итоговые метрики
                self._print_summary()
        
        except Exception as e:
            print_colored(f"\n❌ Connection error: {e}", Colors.RED)
            import traceback
            traceback.print_exc()
    
    async def _handle_message(self, message: Dict[str, Any]):
        """Обработка полученного сообщения."""
        
        current_time = time.time() - self.start_time
        
        if message.get('status') == 'processing':
            print_colored(f"\n⏳ [{current_time:.1f}s] {message.get('message')}", Colors.YELLOW)
        
        elif message.get('type') == 'progress':
            event_type = message.get('event_type')
            data = message.get('data', {})
            
            if event_type == 'detection_started':
                print_colored(f"\n🔍 [{current_time:.1f}s] Detection started...", Colors.CYAN)
            
            elif event_type == 'regions_detected':
                self.regions_count = data.get('total_regions', 0)
                print_colored(
                    f"\n📍 [{current_time:.1f}s] Regions detected: {self.regions_count}",
                    Colors.GREEN + Colors.BOLD
                )
                
                # Показываем первые 3 области
                regions = data.get('regions', [])
                for i, region in enumerate(regions[:3]):
                    coords = region.get('coordinates', [])
                    print_colored(f"   Region {i}: {len(coords)} points", Colors.BLUE)
            
            elif event_type == 'region_ocr_started':
                region_idx = data.get('region_index')
                print_colored(f"   🔄 [{current_time:.1f}s] OCR started: Region {region_idx}", Colors.CYAN)
            
            elif event_type == 'region_ocr_completed':
                if self.first_result_time is None:
                    self.first_result_time = current_time
                
                self.ocr_completed += 1
                region_idx = data.get('region_index')
                text = data.get('original_text', '')
                confidence = data.get('confidence', 0.0)
                
                # Показываем первые 40 символов текста
                text_preview = text[:40] + "..." if len(text) > 40 else text
                
                print_colored(
                    f"   📝 [{current_time:.1f}s] OCR #{region_idx} (conf: {confidence:.2f}): {text_preview}",
                    Colors.GREEN
                )
            
            elif event_type == 'region_ocr_failed':
                self.errors_count += 1
                region_idx = data.get('region_index')
                error = data.get('error_message', 'Unknown error')
                print_colored(f"   ❌ [{current_time:.1f}s] OCR failed: Region {region_idx} - {error}", Colors.RED)
            
            elif event_type == 'region_translation_started':
                region_idx = data.get('region_index')
                print_colored(f"   🔄 [{current_time:.1f}s] Translation started: Region {region_idx}", Colors.CYAN)
            
            elif event_type == 'region_translated':
                self.translations_completed += 1
                region_idx = data.get('region_index')
                original = data.get('original_text', '')
                translated = data.get('translated_text', '')
                
                # Показываем первые 30 символов
                original_preview = original[:30] + "..." if len(original) > 30 else original
                translated_preview = translated[:30] + "..." if len(translated) > 30 else translated
                
                print_colored(
                    f"   🌐 [{current_time:.1f}s] Translation #{region_idx}:",
                    Colors.GREEN + Colors.BOLD
                )
                print_colored(f"      Original:    {original_preview}", Colors.BLUE)
                print_colored(f"      Translated:  {translated_preview}", Colors.GREEN)
            
            elif event_type == 'region_translation_failed':
                self.errors_count += 1
                region_idx = data.get('region_index')
                error = data.get('error_message', 'Unknown error')
                print_colored(
                    f"   ❌ [{current_time:.1f}s] Translation failed: Region {region_idx} - {error}",
                    Colors.RED
                )
            
            elif event_type == 'processing_completed':
                print_colored(f"\n✅ [{current_time:.1f}s] Processing completed!", Colors.GREEN + Colors.BOLD)
                summary = data
                print_colored(f"   Total regions: {summary.get('total_regions')}", Colors.BLUE)
                print_colored(f"   Processed: {summary.get('successfully_processed')}", Colors.GREEN)
                print_colored(f"   Failed: {summary.get('failed_regions')}", Colors.RED if summary.get('failed_regions') > 0 else Colors.GREEN)
        
        elif message.get('type') == 'completed':
            total_time = time.time() - self.start_time
            summary = message.get('summary', {})
            
            print_section("✅ PROCESSING COMPLETED")
            print_colored(f"Total regions: {summary.get('total_regions')}", Colors.BLUE)
            print_colored(f"Translated: {summary.get('translated_regions')}", Colors.GREEN)
            print_colored(f"Total time: {summary.get('total_processing_time', total_time):.2f}s", Colors.CYAN)
    
    def _print_summary(self):
        """Вывод итоговых метрик."""
        
        total_time = time.time() - self.start_time
        
        print_section("📊 PERFORMANCE METRICS")
        
        print_colored(f"⏱️  Total processing time: {total_time:.2f}s", Colors.BOLD + Colors.CYAN)
        
        if self.first_result_time:
            print_colored(
                f"⚡ Time to first result: {self.first_result_time:.2f}s",
                Colors.BOLD + Colors.GREEN
            )
        
        print_colored(f"\n📍 Regions detected: {self.regions_count}", Colors.BLUE)
        print_colored(f"📝 OCR completed: {self.ocr_completed}", Colors.GREEN)
        print_colored(f"🌐 Translations completed: {self.translations_completed}", Colors.GREEN)
        
        if self.errors_count > 0:
            print_colored(f"❌ Errors: {self.errors_count}", Colors.RED)
        else:
            print_colored(f"✅ No errors", Colors.GREEN)
        
        # Производительность
        if self.regions_count > 0 and total_time > 0:
            regions_per_sec = self.regions_count / total_time
            print_colored(f"\n⚡ Throughput: {regions_per_sec:.2f} regions/sec", Colors.CYAN)
        
        print("\n" + "="*60 + "\n")


async def main():
    """Главная функция."""
    
    parser = argparse.ArgumentParser(
        description="Streaming WebSocket API Tester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Простой тест
  python test_streaming_websocket.py image.jpg
  
  # Тест с регионами
  python test_streaming_websocket.py image.jpg --mode regions --regions regions.json
  
  # Другой сервер
  python test_streaming_websocket.py image.jpg --host localhost --port 8001
  
  # С другими языками
  python test_streaming_websocket.py image.jpg --from-lang en --to-lang ru

Примечание: количество воркеров зафиксировано (OCR=1, Translation=2)
        """
    )
    
    parser.add_argument('image', type=str, help='Path to image file')
    parser.add_argument('--host', default='localhost', help='WebSocket host (default: localhost)')
    parser.add_argument('--port', type=int, default=8000, help='WebSocket port (default: 8000)')
    parser.add_argument(
        '--mode',
        choices=['image', 'regions'],
        default='image',
        help='Processing mode (default: image)'
    )
    parser.add_argument('--from-lang', default='zh', help='Source language (default: zh)')
    parser.add_argument('--to-lang', default='ru', help='Target language (default: ru)')
    parser.add_argument('--regions', type=str, help='Path to regions JSON file (for regions mode)')
    
    args = parser.parse_args()
    
    # Проверка файла изображения
    image_path = Path(args.image)
    if not image_path.exists():
        print_colored(f"❌ Error: Image file not found: {image_path}", Colors.RED)
        sys.exit(1)
    
    # Построение URL
    if args.mode == 'image':
        endpoint = '/ws/docs-translate/process-streaming'
    else:
        endpoint = '/ws/docs-translate/process-regions-streaming'
    
    url = f"ws://{args.host}:{args.port}{endpoint}"
    
    # Создание тестера
    tester = StreamingWebSocketTester(
        url=url,
        image_path=image_path,
        from_lang=args.from_lang,
        to_lang=args.to_lang,
        mode=args.mode
    )
    
    # Запуск теста
    if args.mode == 'image':
        await tester.test_process_image_streaming()
    else:
        # Загрузка регионов
        if not args.regions:
            print_colored("❌ Error: --regions required for regions mode", Colors.RED)
            sys.exit(1)
        
        regions_path = Path(args.regions)
        if not regions_path.exists():
            print_colored(f"❌ Error: Regions file not found: {regions_path}", Colors.RED)
            sys.exit(1)
        
        with open(regions_path, 'r') as f:
            regions = json.load(f)
        
        await tester.test_process_regions_streaming(regions)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_colored("\n\n⚠️  Test interrupted by user", Colors.YELLOW)
        sys.exit(0)

