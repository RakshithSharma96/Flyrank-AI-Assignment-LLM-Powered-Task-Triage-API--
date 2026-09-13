import json
import urllib.request

API_URL = "http://127.0.0.1:8000/triage"


def call_api(text):
    payload = json.dumps({"text": text}).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    with open("evals/cases.json", "r", encoding="utf-8") as file:
        cases = json.load(file)

    matched = 0
    failures = []

    for index, case in enumerate(cases, start=1):
        try:
            result = call_api(case["input"])
            actual = result["category"]
            expected = case["expected_category"]

            if actual == expected:
                matched += 1
            else:
                failures.append(
                    {
                        "case": index,
                        "expected": expected,
                        "actual": actual,
                        "input": case["input"],
                    }
                )

        except Exception as error:
            failures.append(
                {
                    "case": index,
                    "error": str(error),
                    "input": case["input"],
                }
            )

    percentage = matched / len(cases) * 100

    print(f"Matched: {matched}/{len(cases)}")
    print(f"Category accuracy: {percentage:.1f}%")

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(json.dumps(failure, indent=2))
    else:
        print("\nFailures: none")


if __name__ == "__main__":
    main()