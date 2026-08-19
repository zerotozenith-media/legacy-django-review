import os
import google.generativeai as genai

# Configure the generative AI model
genai.configure(api_key=os.environ['GEMINI_API_KEY'])
generation_config = {
    "temperature": 0,
    "top_p": 0.95,
    "top_k": 0,
    "max_output_tokens": 8192,
}
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]


train1 = """TD Home | Apply | My Profile
Logout
Site Search
Interac e-Transfer® - History
Account
Church Saving - 52526224547 ▼
Help
| Print
Money Sent
Money Requested
Money Received
Custom Date ▼
DEEPER CHRISTIAN LIFE MINISTRY CANADA ▼
Month-Year
Custom Date Range
Select Month ▼
Select Year ▼
June 1, 2024
Oct 7, 2024
Search
Date
Received From
Amount
Method
Status
Feb 11, 2024
Ryan E. Morris
$1,017.00
Email/Mobile
Autodeposited
Sep 05, 2024
Sabrina Erica Park
$1,559.00
Email/Mobile
Autodeposited
Mar 01, 2024
Thomas Neal
$991.00
Email/Mobile
Autodeposited
Apr 20, 2024
Kelsey Christopher Thompson
$1,445.00
Email/Mobile
Autodeposited
Jan 11, 2024
Gregory David Carter
$411.00
Email/Mobile
Autodeposited


"""
train2 = """TD Home | Apply | My Profile
Logout
Site Search
Interac e-Transfer® - History
Account
Church Saving - 52526224547 ▼
Help
| Print
Money Sent
Money Requested
Money Received
Custom Date ▼
DEEPER CHRISTIAN LIFE MINISTRY CANADA ▼
Month-Year
Custom Date Range
Select Month ▼
Select Year ▼
June 1, 2024
Oct 7, 2024
Search
Date
Received From
Amount
Method
Status
Sep 02, 2024
Shawn Steven Perry
$1,662.00
Email/Mobile
Autodeposited
Jun 15, 2024
Kevin Sullivan
$466.00
Email/Mobile
Autodeposited

"""
train3 = """TD Home | Apply | My Profile
Logout
Site Search
Interac e-Transfer® - History
Account
Church Saving - 52526224547 ▼
Help
| Print
Money Sent
Money Requested
Money Received
Custom Date ▼
DEEPER CHRISTIAN LIFE MINISTRY CANADA ▼
Month-Year
Custom Date Range
Select Month ▼
Select Year ▼
June 1, 2024
Oct 7, 2024
Search
Date
Received From
Amount
Method
Status
Jul 31, 2024
Douglas Kelsey Delgado
$476.00
Email/Mobile
Autodeposited
Aug 20, 2024
Julia E. Benson
$811.00
Email/Mobile
Autodeposited
Aug 19, 2024
Robert James Lewis
$1,363.00
Email/Mobile
Autodeposited

"""
example_output1 = '[{"name": "Ryan E. Morris", "date": "Feb 11, 2024", "amount": "$1,017.00", "method": "Email/Mobile", "status": "Autodeposited"}, {"name": "Sabrina Erica Park", "date": "Sep 05, 2024", "amount": "$1,559.00", "method": "Email/Mobile", "status": "Autodeposited"}, {"name": "Thomas Neal", "date": "Mar 01, 2024", "amount": "$991.00", "method": "Email/Mobile", "status": "Autodeposited"}, {"name": "Kelsey Christopher Thompson", "date": "Apr 20, 2024", "amount": "$1,445.00", "method": "Email/Mobile", "status": "Autodeposited"}, {"name": "Gregory David Carter", "date": "Jan 11, 2024", "amount": "$411.00", "method": "Email/Mobile", "status": "Autodeposited"}]'
example_output2 = '[{"name": "Shawn Steven Perry", "date": "Sep 02, 2024", "amount": "$1,662.00", "method": "Email/Mobile", "status": "Autodeposited"}, {"name": "Kevin Sullivan", "date": "Jun 15, 2024", "amount": "$466.00", "method": "Email/Mobile", "status": "Autodeposited"}]'
example_output3 = '[{"name": "Douglas Kelsey Delgado", "date": "Jul 31, 2024", "amount": "$476.00", "method": "Email/Mobile", "status": "Autodeposited"}, {"name": "Julia E. Benson", "date": "Aug 20, 2024", "amount": "$811.00", "method": "Email/Mobile", "status": "Autodeposited"}, {"name": "Robert James Lewis", "date": "Aug 19, 2024", "amount": "$1,363.00", "method": "Email/Mobile", "status": "Autodeposited"}]'

example_documents = [
    train1,
    train2,
    train3
]
example_outputs = [
    example_output1,
    example_output2,
    example_output3
]
labels = ["name", "date", "amount", "method", "status"]
label_text = ','.join(labels)


def doc_intelligence(document):

    system_instruction = f"""
    You are a highly intelligent language model. Your task is to extract key-value pairs from a bank statement document based on the specified keys. 
    Use the following example documents and their corresponding key-value pairs to learn the structure and format.
     
    Following are 3 example documents and outputs.
    Example Document 1:
    {example_documents[0]}

    Example Output 1:
    {example_outputs[0]}

    Example Document 2:
    {example_documents[1]}

    Example Output 2:
    {example_outputs[1]}

    Example Document 3:
    {example_documents[2]}

    Example Output 3:
    {example_outputs[2]}

    when provided with a document "{document}" and a set of keys "{label_text}", you will extract and return the corresponding values.
    You will return a list of all extracted key-value pairs representing transactions in the following JSON format:
        {
            [
                {
                    "name": "Ryan E. Morris",
                    "date": "Feb 11, 2024",
                    "amount": "$1,017.00",
                    "method": "Email/Mobile",
                    "status": "Autodeposited"
                },
                {
                    "name": "Sabrina Erica Park",
                    "date": "Sep 05, 2024",
                    "amount": "$1,559.00",
                    "method": "Email/Mobile",
                    "status": "Autodeposited"
                },
                ...
            ]
        }
        Ensure you return valid json string, the quotes must be double quotes, otherwise in Python json.loads will fail.
        Return pure json text string without markdown so that I can use json.loads to parse it directly.
    """

    model = genai.GenerativeModel(
        # model_name="gemini-1.5-pro",
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction=system_instruction,
    )

    converse = model.start_chat()
    converse.send_message(label_text)
    response = converse.last.text
    return response
