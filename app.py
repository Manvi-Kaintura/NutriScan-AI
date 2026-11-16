            if value is None:
                return "Not available"
            return f"{round(value, 1):g} {unit}"

        sodium = get_number(nutrients, "sodium_100g")
        sodium_display = (
            f"{round(sodium * 1000, 1):g} mg"
            if sodium is not None else "Not available"
        )

        product_data = {
            "barcode": barcode,
            "name": product.get("product_name", "Unknown Product"),
            "brand": product.get("brands", "Not available"),
            "calories": get_value("energy-kcal_100g", "kcal"),
            "protein": get_value("proteins_100g", "g"),
            "carbs": get_value("carbohydrates_100g", "g"),
            "fat": get_value("fat_100g", "g"),
            "fibre": get_value("fiber_100g", "g"),
            "sugar": get_value("sugars_100g", "g"),
            "saturated_fat": get_value("saturated-fat_100g", "g"),
            "sodium": sodium_display,
            "protein_value": get_number(nutrients, "proteins_100g"),
            "carbs_value": get_number(nutrients, "carbohydrates_100g"),
            "fat_value": get_number(nutrients, "fat_100g"),
            "score": calculate_score(nutrients)
        }

        try:
            save_scan(product_data, session["user_id"])
            print("Product saved for user:", session["user_id"])
        except psycopg2.Error as error:
            print("Database Save Error:", repr(error))
            return jsonify({
                "error": "Product was found, but could not be saved. Please try again."
            }), 500

        return jsonify(product_data)

    except requests.RequestException as error:
        print("Food Database Error:", repr(error))
        return jsonify({
            "error": "Food database is temporarily unavailable."
        }), 503


# =====================================================
# GEMINI AI SUMMARY
# =====================================================

@app.route("/summary", methods=["POST"])
@login_required
def summary():
    if client is None:
        return jsonify({"summary": "Gemini API key is missing."}), 500

    product = request.get_json(silent=True) or {}
    prompt = f"""
    Analyse this food product using only the supplied information.

    Product: {product.get('name')}
    Brand: {product.get('brand')}

    Nutrition per 100g:
    Calories: {product.get('calories')}
    Protein: {product.get('protein')}
    Carbohydrates: {product.get('carbs')}
    Fat: {product.get('fat')}
    Fibre: {product.get('fibre')}
    Sugar: {product.get('sugar')}

    Write a concise summary in simple English.

    Include:
    1. Overall overview
    2. Nutritional advantages
    3. Nutritional disadvantages
    4. Regular consumption

    Use short bullet points.
    Do not invent missing values.
    Avoid medical claims.
    Keep the answer under 150 words.
    """

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt
            )
            if not response.text:
                raise ValueError("Gemini returned an empty response.")
            return jsonify({"summary": response.text})
        except Exception as error:
            print(f"Gemini Error (Attempt {attempt + 1}/3):", repr(error))
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))

    return jsonify({
        "summary": "AI analysis is temporarily unavailable."
    }), 503


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)
