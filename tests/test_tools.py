"""Tests for JARVIS tools (no API key required)."""

import pytest

from jarvis.tools.calculator import calculator_tool
from jarvis.tools.code_executor import code_executor_tool
from jarvis.tools.file_manager import file_manager_tool
from jarvis.tools.system_info import system_info_tool


class TestCalculator:
    """Test suite for the calculator tool."""

    def test_basic_addition(self):
        result = calculator_tool("2 + 2")
        assert "4" in result

    def test_basic_subtraction(self):
        result = calculator_tool("10 - 3")
        assert "7" in result

    def test_basic_multiplication(self):
        result = calculator_tool("6 * 7")
        assert "42" in result

    def test_basic_division(self):
        result = calculator_tool("15 / 3")
        assert "5" in result

    def test_square_root(self):
        result = calculator_tool("sqrt(144)")
        assert "12" in result

    def test_power(self):
        result = calculator_tool("2 ** 10")
        assert "1024" in result

    def test_pi_constant(self):
        result = calculator_tool("pi")
        assert "3.14" in result

    def test_trigonometry(self):
        result = calculator_tool("sin(pi/2)")
        assert "1" in result

    def test_logarithm(self):
        result = calculator_tool("log10(1000)")
        assert "3" in result

    def test_factorial(self):
        result = calculator_tool("factorial(5)")
        assert "120" in result

    def test_zero_division(self):
        result = calculator_tool("1 / 0")
        assert "zero" in result.lower() or "❌" in result

    def test_invalid_expression(self):
        result = calculator_tool("not_a_math_expression")
        assert "❌" in result

    def test_dangerous_expression_blocked(self):
        result = calculator_tool("__import__('os').system('ls')")
        assert "❌" in result

    def test_complex_expression(self):
        result = calculator_tool("(2 + 3) * (4 - 1) / sqrt(9)")
        assert "5" in result


class TestCodeExecutor:
    """Test suite for the code executor tool."""

    def test_simple_print(self):
        result = code_executor_tool("print('Hello, World!')")
        assert "Hello, World!" in result
        assert "✅" in result

    def test_arithmetic_output(self):
        result = code_executor_tool("print(2 + 2)")
        assert "4" in result

    def test_variable_assignment(self):
        result = code_executor_tool("x = 42\nprint(x)")
        assert "42" in result

    def test_loop(self):
        result = code_executor_tool("for i in range(3):\n    print(i)")
        assert "0" in result
        assert "1" in result
        assert "2" in result

    def test_function_definition(self):
        result = code_executor_tool(
            "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)\nprint(factorial(5))"
        )
        assert "120" in result

    def test_syntax_error(self):
        result = code_executor_tool("def broken(:\n    pass")
        assert "❌" in result
        assert "Syntax" in result

    def test_runtime_error(self):
        result = code_executor_tool("x = 1 / 0")
        assert "❌" in result

    def test_no_output(self):
        result = code_executor_tool("x = 5")
        assert "✅" in result
        assert "No output" in result

    def test_unsupported_language(self):
        result = code_executor_tool("console.log('hi')", language="javascript")
        assert "not supported" in result.lower()

    def test_list_comprehension(self):
        result = code_executor_tool("print([x**2 for x in range(5)])")
        assert "0" in result
        assert "16" in result

    def test_string_operations(self):
        result = code_executor_tool("s = 'JARVIS'\nprint(s.lower())")
        assert "jarvis" in result

    def test_math_import(self):
        result = code_executor_tool("import math\nprint(math.pi)")
        assert "3.14" in result


class TestFileManager:
    """Test suite for the file manager tool."""

    def test_write_and_read(self, tmp_path):
        """Test writing and reading a file."""
        test_file = str(tmp_path / "test.txt")
        write_result = file_manager_tool("write", test_file, content="Hello JARVIS!")
        assert "✅" in write_result

        read_result = file_manager_tool("read", test_file)
        assert "Hello JARVIS!" in read_result

    def test_append(self, tmp_path):
        """Test appending to a file."""
        test_file = str(tmp_path / "append_test.txt")
        file_manager_tool("write", test_file, content="Line 1\n")
        file_manager_tool("append", test_file, content="Line 2\n")
        read_result = file_manager_tool("read", test_file)
        assert "Line 1" in read_result
        assert "Line 2" in read_result

    def test_list_directory(self, tmp_path):
        """Test listing directory contents."""
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        result = file_manager_tool("list", str(tmp_path))
        assert "file1.txt" in result
        assert "file2.txt" in result

    def test_exists_true(self, tmp_path):
        """Test checking existence of existing file."""
        test_file = tmp_path / "existing.txt"
        test_file.write_text("exists")
        result = file_manager_tool("exists", str(test_file))
        assert "Exists" in result

    def test_exists_false(self, tmp_path):
        """Test checking existence of non-existing file."""
        result = file_manager_tool("exists", str(tmp_path / "nonexistent.txt"))
        assert "not exist" in result.lower()

    def test_read_nonexistent(self, tmp_path):
        """Test reading non-existent file."""
        result = file_manager_tool("read", str(tmp_path / "missing.txt"))
        assert "❌" in result
        assert "not found" in result.lower()

    def test_delete_file(self, tmp_path):
        """Test deleting a file."""
        test_file = tmp_path / "to_delete.txt"
        test_file.write_text("delete me")
        result = file_manager_tool("delete", str(test_file))
        assert "✅" in result
        assert not test_file.exists()

    def test_file_info(self, tmp_path):
        """Test getting file info."""
        test_file = tmp_path / "info_test.txt"
        test_file.write_text("some content")
        result = file_manager_tool("info", str(test_file))
        assert "File" in result
        assert "bytes" in result.lower()

    def test_invalid_operation(self, tmp_path):
        """Test unknown operation."""
        result = file_manager_tool("invalid_op", str(tmp_path))
        assert "❌" in result
        assert "Unknown operation" in result


class TestSystemInfo:
    """Test suite for the system info tool."""

    def test_datetime(self):
        result = system_info_tool("datetime")
        assert "Date" in result or "Time" in result

    def test_date(self):
        result = system_info_tool("date")
        assert "📅" in result

    def test_time(self):
        result = system_info_tool("time")
        assert "🕐" in result

    def test_platform(self):
        result = system_info_tool("platform")
        assert "OS" in result or "System" in result

    def test_all(self):
        result = system_info_tool("all")
        assert len(result) > 50  # Should contain substantial info

    def test_unknown_type(self):
        result = system_info_tool("unknown_type")
        assert "Unknown" in result
