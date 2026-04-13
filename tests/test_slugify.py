"""Tests for slugify utility function."""

import pytest

from src.Ship.Core.Utils import slugify


class TestSlugify:
    """Test cases for slugify function."""
    
    def test_basic_latin_input(self):
        """Test basic Latin text slugification."""
        assert slugify("Hello World") == "hello-world"
        assert slugify("This is a test") == "this-is-a-test"
        assert slugify("UPPERCASE TEXT") == "uppercase-text"
    
    def test_cyrillic_input(self):
        """Test Cyrillic text transliteration and slugification."""
        assert slugify("Привет мир") == "privet-mir"
        assert slugify("Это тест") == "eto-test"
        assert slugify("Москва") == "moskva"
        assert slugify("Санкт-Петербург") == "sankt-peterburg"
    
    def test_mixed_latin_cyrillic(self):
        """Test mixed Latin and Cyrillic text."""
        assert slugify("Hello, мир!") == "hello-mir"
        assert slugify("Test тест 123") == "test-test-123"
        assert slugify("Python и питон") == "python-i-piton"
    
    def test_special_cyrillic_characters(self):
        """Test special Cyrillic characters transliteration."""
        assert slugify("ёжик") == "ezhik"
        assert slugify("щука") == "shchuka"
        assert slugify("объект") == "obekt"
        assert slugify("мягкий") == "myagkiy"
    
    def test_punctuation_and_special_chars(self):
        """Test handling of punctuation and special characters."""
        assert slugify("Hello, World!") == "hello-world"
        assert slugify("test@example.com") == "testexamplecom"
        assert slugify("price: $100") == "price-100"
        assert slugify("C++ Programming") == "c-programming"
    
    def test_multiple_spaces_and_hyphens(self):
        """Test handling of multiple spaces and hyphens."""
        assert slugify("Hello   World") == "hello-world"
        assert slugify("test---slug") == "test-slug"
        assert slugify("  leading spaces") == "leading-spaces"
        assert slugify("trailing spaces  ") == "trailing-spaces"
    
    def test_leading_trailing_hyphens(self):
        """Test removal of leading and trailing hyphens."""
        assert slugify("-hello-world-") == "hello-world"
        assert slugify("---test---") == "test"
        assert slugify("- - - test - - -") == "test"
    
    def test_numbers(self):
        """Test handling of numbers."""
        assert slugify("123") == "123"
        assert slugify("test 123 test") == "test-123-test"
        assert slugify("2024 год") == "2024-god"
    
    def test_empty_and_whitespace(self):
        """Test empty string and whitespace handling."""
        assert slugify("") == ""
        assert slugify("   ") == ""
        assert slugify("\n\t") == ""
    
    def test_unicode_normalization(self):
        """Test Unicode normalization."""
        assert slugify("café") == "cafe"
        assert slugify("naïve") == "naive"
        assert slugify("résumé") == "resume"
    
    def test_all_cyrillic_letters(self):
        """Test all Cyrillic letters transliteration."""
        # Lowercase
        assert slugify("абвгдеёжзийклмнопрстуфхцчшщъыьэюя") == "abvgdeezhziyklmnoprstufhtschshshchyeyuya"
        # Uppercase
        assert slugify("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ") == "abvgdeezhziyklmnoprstufhtschshshchyeyuya"
    
    def test_real_world_examples(self):
        """Test real-world use cases."""
        assert slugify("Новый продукт 2024!") == "novyy-produkt-2024"
        assert slugify("Скидка 50%!!!") == "skidka-50"
        assert slugify("FAQ: Часто задаваемые вопросы") == "faq-chasto-zadavaemye-voprosy"
        assert slugify("E-mail: info@example.com") == "e-mail-infoexamplecom"
