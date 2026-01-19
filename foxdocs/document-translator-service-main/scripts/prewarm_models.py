import os
import asyncio
from pathlib import Path


def check_paddleocr_models_exist() -> bool:
    """Проверяем наличие основных моделей PaddleOCR локально."""
    # PaddleOCR может использовать разные пути кеширования
    possible_cache_paths = [
        # Новый формат PaddleX (как видно из логов)
        Path("/app/.paddlex/official_models"),
        # Старый формат PaddleOCR
        Path(os.environ.get("XDG_CACHE_HOME", "/app/.cache")) / "paddle" / "whl",
        # Альтернативный путь в HOME
        Path(os.environ.get("HOME", "/app")) / ".paddleocr",
    ]
    
    # Ищем основные модели, которые используются в проекте
    required_models = [
        "PP-OCRv5_server_det",  # Детекция текста
        "PP-OCRv5_server_rec",  # Распознавание текста
    ]
    
    for cache_path in possible_cache_paths:
        if not cache_path.exists():
            continue
            
        models_found = 0
        for model_name in required_models:
            # Ищем директории с именем модели
            model_dirs = list(cache_path.rglob(f"*{model_name}*"))
            if model_dirs:
                # Проверяем наличие файлов модели (.pdmodel, .pdiparams и т.д.)
                for model_dir in model_dirs:
                    if model_dir.is_dir() and (
                        any(model_dir.glob("*.pdmodel")) or
                        any(model_dir.glob("*.pdiparams")) or
                        any(model_dir.glob("inference.pdmodel"))
                    ):
                        models_found += 1
                        break
        
        # Если нашли все требуемые модели в одном из путей кеша
        if models_found >= len(required_models):
            return True
    
    return False


def prewarm_paddleocr() -> None:
    """Предзагружаем модели PaddleOCR только если их нет локально."""
    import sys
    
    print("=" * 60)
    print("STARTING PADDLEOCR MODELS DOWNLOAD")
    print("=" * 60)
    sys.stdout.flush()
    
    # Настраиваем кеши внутри контейнера
    os.makedirs("/app/.cache/paddle", exist_ok=True)
    os.environ.setdefault("HOME", "/app")
    os.environ.setdefault("XDG_CACHE_HOME", "/app/.cache")
    
    print(f"Cache directory: /app/.cache/paddle")
    print(f"HOME: {os.environ.get('HOME')}")
    print(f"XDG_CACHE_HOME: {os.environ.get('XDG_CACHE_HOME')}")
    sys.stdout.flush()
    
    # Проверяем наличие моделей
    print("\nChecking for existing PaddleOCR models...")
    sys.stdout.flush()
    
    if check_paddleocr_models_exist():
        print("✓ PaddleOCR models already exist locally, skipping download")
        print("=" * 60)
        sys.stdout.flush()
        return
    
    print("✗ PaddleOCR models not found, downloading...")
    sys.stdout.flush()
    
    try:
        print("\n[1/3] Importing PaddleOCR modules...")
        sys.stdout.flush()
        
        # Импортируем здесь, чтобы не тянуть при импорте модуля
        from paddleocr import PaddleOCR, TextRecognition
        
        print("✓ PaddleOCR modules imported successfully")
        sys.stdout.flush()

        # Создадим инстанс, чтобы все веса/модели скачались при инициализации
        # lang='ch' используется в проекте
        print("\n[2/3] Initializing PaddleOCR instance (will download models)...")
        print("This may take several minutes...")
        sys.stdout.flush()
        
        ocr = PaddleOCR(
            use_angle_cls=False,
            lang="ch",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
        )
        
        print("✓ PaddleOCR instance initialized")
        sys.stdout.flush()

        # Дополнительно прогреем TextRecognition конкретной моделью
        print("\n[3/3] Initializing TextRecognition (PP-OCRv5_server_rec)...")
        sys.stdout.flush()
        
        _ = TextRecognition(model_name="PP-OCRv5_server_rec")
        
        print("✓ TextRecognition initialized")
        print("\n✓ PaddleOCR models downloaded successfully")
        sys.stdout.flush()
        
    except Exception as e:
        print(f"\n✗ Failed to download PaddleOCR models: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        # Не падаем, просто логируем - модели скачаются в runtime
    
    print("=" * 60)
    print("FINISHED PADDLEOCR MODELS DOWNLOAD")
    print("=" * 60)
    sys.stdout.flush()


def check_argos_packages_exist() -> bool:
    """Проверяем наличие требуемых пакетов Argos локально."""
    import argostranslate.package
    
    required = [("zh", "en"), ("en", "ru")]
    installed = argostranslate.package.get_installed_packages()
    
    for from_code, to_code in required:
        if not any((pkg.from_code, pkg.to_code) == (from_code, to_code) for pkg in installed):
            return False
    
    return True


async def prewarm_argos() -> None:
    """Предзагружаем пакеты Argos только если их нет локально."""
    import sys
    import argostranslate.package
    
    print("=" * 60)
    print("STARTING ARGOS TRANSLATION PACKAGES DOWNLOAD")
    print("=" * 60)
    sys.stdout.flush()

    # В контейнере положим данные в /app/.argos
    os.environ.setdefault("ARGOS_DATA_DIR", "/app/.argos")
    os.makedirs("/app/.argos", exist_ok=True)
    
    print(f"Argos data directory: /app/.argos")
    print(f"Directory exists: {os.path.exists('/app/.argos')}")
    print(f"Directory is writable: {os.access('/app/.argos', os.W_OK)}")
    sys.stdout.flush()

    # Проверяем наличие пакетов
    print("\nChecking for existing Argos packages...")
    sys.stdout.flush()
    
    if check_argos_packages_exist():
        print("✓ Argos translation packages already exist locally, skipping download")
        print("=" * 60)
        sys.stdout.flush()
        return
    
    print("✗ Argos translation packages not found, downloading...")
    sys.stdout.flush()

    try:
        # Попробуем обновить индекс (он небольшой). Если офлайн — пропустим.
        print("\n[1/3] Updating Argos package index...")
        sys.stdout.flush()
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, argostranslate.package.update_package_index
            )
            print("✓ Argos package index updated")
            sys.stdout.flush()
        except Exception as e:
            print(f"⚠ Failed to update Argos package index: {e}")
            print("Trying with cached data...")
            sys.stdout.flush()

        # Набор пакетов, требуемых приложением
        required = [("zh", "en"), ("en", "ru")]
        
        print(f"\n[2/3] Required packages: {required}")
        sys.stdout.flush()

        # Проверим, что пакеты установлены; если нет — установим
        def _install_all():
            print("\n[3/3] Installing translation packages...")
            sys.stdout.flush()
            
            available = argostranslate.package.get_available_packages()
            print(f"Available packages count: {len(available)}")
            sys.stdout.flush()
            
            by_pair = {}
            for p in available:
                by_pair.setdefault((p.from_code, p.to_code), []).append(p)

            for pair in required:
                print(f"\nProcessing package {pair[0]}->{pair[1]}...")
                sys.stdout.flush()
                
                # уже установлено?
                installed = argostranslate.package.get_installed_packages()
                if any((pkg.from_code, pkg.to_code) == pair for pkg in installed):
                    print(f"✓ Package {pair[0]}->{pair[1]} already installed")
                    sys.stdout.flush()
                    continue

                candidates = by_pair.get(pair) or []
                if not candidates:
                    # нет в индексе — пропускаем (возможен офлайн)
                    print(f"✗ Package {pair[0]}->{pair[1]} not found in available packages")
                    sys.stdout.flush()
                    continue
                    
                # выберем первый (обычно самый новый)
                pkg = candidates[0]
                print(f"Downloading package {pair[0]}->{pair[1]}...")
                sys.stdout.flush()
                
                path = pkg.download()
                print(f"Installing package from {path}...")
                sys.stdout.flush()
                
                argostranslate.package.install_from_path(path)
                print(f"✓ Installed package {pair[0]}->{pair[1]}")
                sys.stdout.flush()

        await asyncio.get_event_loop().run_in_executor(None, _install_all)
        print("\n✓ Argos translation packages downloaded successfully")
        sys.stdout.flush()
        
    except Exception as e:
        print(f"\n✗ Failed to download Argos packages: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        # Не падаем, просто логируем - пакеты скачаются в runtime
    
    print("=" * 60)
    print("FINISHED ARGOS TRANSLATION PACKAGES DOWNLOAD")
    print("=" * 60)
    sys.stdout.flush()


def prewarm_stanza() -> None:
    """Предзагружаем модели Stanza для токенизации."""
    import os
    import sys
    
    print("=" * 60)
    print("STARTING STANZA MODELS DOWNLOAD")
    print("=" * 60)
    
    os.environ.setdefault("STANZA_RESOURCES_DIR", "/app/.stanza")
    os.makedirs("/app/.stanza", exist_ok=True)
    
    print(f"Stanza resources directory: /app/.stanza")
    print(f"Directory exists: {os.path.exists('/app/.stanza')}")
    print(f"Directory is writable: {os.access('/app/.stanza', os.W_OK)}")
    sys.stdout.flush()
    
    try:
        print("\n[1/4] Importing stanza module...")
        sys.stdout.flush()
        import stanza
        print("✓ Stanza module imported successfully")
        sys.stdout.flush()
        
        # Скачиваем модели для китайского и английского языков
        # которые используются в argostranslate
        
        # Китайский для токенизации
        print("\n[2/4] Starting Chinese (zh) model download...")
        print("This may take several minutes depending on network speed...")
        sys.stdout.flush()
        
        try:
            # verbose=True чтобы видеть прогресс
            stanza.download('zh', dir='/app/.stanza', verbose=True)
            print("✓ Stanza Chinese model downloaded successfully")
            sys.stdout.flush()
        except Exception as e:
            print(f"✗ Failed to download Stanza Chinese model: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
        
        # Английский для токенизации
        print("\n[3/4] Starting English (en) model download...")
        print("This may take several minutes depending on network speed...")
        sys.stdout.flush()
        
        try:
            # verbose=True чтобы видеть прогресс
            stanza.download('en', dir='/app/.stanza', verbose=True)
            print("✓ Stanza English model downloaded successfully")
            sys.stdout.flush()
        except Exception as e:
            print(f"✗ Failed to download Stanza English model: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
        
        print("\n[4/4] Stanza download phase complete")
        sys.stdout.flush()
            
    except Exception as e:
        print(f"\n✗ Failed to initialize Stanza: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
    
    print("=" * 60)
    print("FINISHED STANZA MODELS DOWNLOAD")
    print("=" * 60)
    sys.stdout.flush()


def main() -> None:
    import sys
    import time
    
    print("\n" + "=" * 60)
    print("MODEL PREWARMING SCRIPT STARTED")
    print("=" * 60)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")
    sys.stdout.flush()
    
    start_time = time.time()
    
    try:
        # 1. PaddleOCR
        print("\n### STEP 1/3: PaddleOCR ###\n")
        sys.stdout.flush()
        prewarm_paddleocr()
        
        # # 2. Stanza
        # print("\n\n### STEP 2/3: Stanza ###\n")
        # sys.stdout.flush()
        # prewarm_stanza()
        
        # 3. Argos
        print("\n\n### STEP 3/3: Argos Translation ###\n")
        sys.stdout.flush()
        asyncio.run(prewarm_argos())
        
    except Exception as e:
        print(f"\n\n✗ CRITICAL ERROR in main: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        raise
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("MODEL PREWARMING SCRIPT COMPLETED")
    print("=" * 60)
    print(f"Total time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()


