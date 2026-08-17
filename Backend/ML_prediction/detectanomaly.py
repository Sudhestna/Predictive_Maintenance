# from Services.llm import model1,model2,model3,model4,model5
import joblib

model1=joblib.load(r"C:\Users\GenAIHYDSYPUSR35\Desktop\PNC_AI_TEAM\ML_prediction\iforest_r101.pkl")
model2=joblib.load(r"C:\Users\GenAIHYDSYPUSR35\Desktop\PNC_AI_TEAM\ML_prediction\iforest_r102.pkl")
model3=joblib.load(r"C:\Users\GenAIHYDSYPUSR35\Desktop\PNC_AI_TEAM\ML_prediction\iforest_r103.pkl")
model4=joblib.load(r"C:\Users\GenAIHYDSYPUSR35\Desktop\PNC_AI_TEAM\ML_prediction\iforest_r104.pkl")
model5=joblib.load(r"C:\Users\GenAIHYDSYPUSR35\Desktop\PNC_AI_TEAM\ML_prediction\iforest_r105.pkl")


def predict_anomaly(m_id,sensor_data):
    sample=list(sensor_data.values())

    if m_id=="R101":
        result=model1.predict([sample])

    elif m_id=="R102":        
        result=model2.predict([sample])

    elif m_id=="R103":        
        result=model3.predict([sample])

    elif m_id=="R104":        
        result=model4.predict([sample])
        
    elif m_id=="R105":        
        result=model5.predict([sample])

    return result[0]


        
