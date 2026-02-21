
import { GoogleGenAI } from "@google/genai";
import * as dotenv from 'dotenv';
dotenv.config();

async function listModels() {
    const genAI = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
    try {
        const response = await genAI.models.list();
        console.log("Available models:");
        // The SDK response structure might vary, let's inspect the keys or iterate
        if (response && response.models) {
            response.models.forEach(model => {
                console.log(`- ${model.name} (${model.displayName})`);
                console.log(`  Supported methods: ${model.supportedGenerationMethods}`);
            });
        } else {
            console.log("Response structure:", JSON.stringify(response, null, 2));
        }
    } catch (error) {
        console.error("Error listing models:", error);
    }
}

listModels();
