"""
Test suite specifically for parser_llm initialization and parse_results_to_text function
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.simple_text2sql import SimpleText2SQLService
from app.config import settings


def test_parser_llm_initialization():
    """Test that parser_llm is properly initialized"""
    print("\n=== Testing parser_llm Initialization ===")

    try:
        service = SimpleText2SQLService()
        print("✓ Service initialized successfully")

        # Check if parser_llm exists
        assert hasattr(service, 'parser_llm'), "parser_llm attribute not found"
        print("✓ parser_llm attribute exists")

        # Check parser_llm type
        print(f"parser_llm type: {type(service.parser_llm)}")
        print(f"parser_llm: {service.parser_llm}")

        # Try to inspect the model configuration
        if hasattr(service.parser_llm, 'model_id'):
            print(f"Model ID: {service.parser_llm.model_id}")
        if hasattr(service.parser_llm, 'region_name'):
            print(f"Region: {service.parser_llm.region_name}")
        if hasattr(service.parser_llm, 'model_kwargs'):
            print(f"Model kwargs: {service.parser_llm.model_kwargs}")

        print("✓ parser_llm initialized correctly")
        return True

    except Exception as e:
        print(f"✗ Error initializing parser_llm: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_parse_results_to_text_simple():
    """Test parse_results_to_text with simple successful results"""
    print("\n=== Testing parse_results_to_text with Simple Results ===")

    try:
        service = SimpleText2SQLService()

        user_query = "How many operational plants are there?"
        sql_query = "SELECT COUNT(*) as count FROM nuclear_power_plants WHERE StatusId = 3"
        execution_result = {
            "success": True,
            "data": [{"count": 42}],
            "row_count": 1
        }

        print(f"User Query: {user_query}")
        print(f"SQL Query: {sql_query}")
        print(f"Execution Result: {execution_result}")

        print("\nCalling parse_results_to_text...")
        parsed_response = service.parse_results_to_text(
            user_query=user_query,
            sql_query=sql_query,
            execution_result=execution_result
        )

        print(f"\nParsed Response Type: {type(parsed_response)}")
        print(f"Parsed Response: {parsed_response}")

        if parsed_response is None:
            print("✗ parse_results_to_text returned None (LLM call failed)")
            return False
        else:
            print("✓ parse_results_to_text returned a response")
            assert isinstance(parsed_response, str), "Response should be a string"
            assert len(parsed_response) > 0, "Response should not be empty"
            print("✓ Response is valid")
            return True

    except Exception as e:
        print(f"✗ Error in parse_results_to_text: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_parse_results_to_text_error_handling():
    """Test parse_results_to_text with error results"""
    print("\n=== Testing parse_results_to_text Error Handling ===")

    try:
        service = SimpleText2SQLService()

        user_query = "Show me invalid data"
        sql_query = "SELECT * FROM nonexistent_table"
        execution_result = {
            "success": False,
            "error": "Table 'nonexistent_table' doesn't exist"
        }

        print(f"User Query: {user_query}")
        print(f"Execution Result: {execution_result}")

        parsed_response = service.parse_results_to_text(
            user_query=user_query,
            sql_query=sql_query,
            execution_result=execution_result
        )

        print(f"Parsed Response: {parsed_response}")

        assert parsed_response is not None, "Should return error message"
        assert "error" in parsed_response.lower(), "Should mention error"
        print("✓ Error handling works correctly")
        return True

    except Exception as e:
        print(f"✗ Error in error handling test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_parse_results_to_text_empty_results():
    """Test parse_results_to_text with empty results"""
    print("\n=== Testing parse_results_to_text with Empty Results ===")

    try:
        service = SimpleText2SQLService()

        user_query = "Show me plants in Antarctica"
        sql_query = "SELECT * FROM nuclear_power_plants WHERE CountryCode = 'AQ'"
        execution_result = {
            "success": True,
            "data": [],
            "row_count": 0
        }

        print(f"User Query: {user_query}")
        print(f"Execution Result: {execution_result}")

        parsed_response = service.parse_results_to_text(
            user_query=user_query,
            sql_query=sql_query,
            execution_result=execution_result
        )

        print(f"Parsed Response: {parsed_response}")

        if parsed_response is None:
            print("✗ parse_results_to_text returned None for empty results")
            return False

        print("✓ Empty results handled correctly")
        return True

    except Exception as e:
        print(f"✗ Error in empty results test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Parser LLM Diagnostic Tests")
    print("=" * 60)

    # Check configuration
    print("\n=== Configuration Check ===")
    print(f"AWS Region: {settings.aws_region}")
    print(f"Bedrock Model ID: {settings.bedrock_model_id}")
    print(f"AWS Access Key ID: {settings.aws_access_key_id[:10]}..." if settings.aws_access_key_id else "Not set")

    # Run tests
    results = []
    results.append(("Parser LLM Initialization", test_parser_llm_initialization()))
    results.append(("Parse Simple Results", test_parse_results_to_text_simple()))
    results.append(("Parse Error Results", test_parse_results_to_text_error_handling()))
    results.append(("Parse Empty Results", test_parse_results_to_text_empty_results()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed")
        sys.exit(1)
