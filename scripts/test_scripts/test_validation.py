from backend.app.sympy_skeletons import validate_answer
print("12 vs 12 puntos:", validate_answer("12", "12 puntos"))
print("12 vs 12:", validate_answer("12", "12"))
print("12 vs labindalawa (12):", validate_answer("12", "labindalawa (12)"))
print("12 puntos vs 12 puntos:", validate_answer("12 puntos", "12 puntos"))
