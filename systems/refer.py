class Refer:
    phone_number : str = "+65 8686 8592"
    call_link : str = "tel:+65 8686 8592"
    whatsapp_chat_link : str = "https://wa.me/6588000554"
    email_address : str = "hello@psychologyblossom.com"
    main_webpage : str = "https://psychologyblossom.com/"
    contact_us_webpage : str = "https://psychologyblossom.com/contact-us/"
    address : str = "150 Cecil Street #07-02, Wing on Life Building, Singapore 069543"
    
    def main(self, **kwargs) -> str:
        return \
        "Referral Information. Render this information in HTML. " \
        f"Phone number: {self.phone_number}, " \
        f"Call Link: {self.call_link}, " \
        f"Whatsapp Chat Link: {self.whatsapp_chat_link}. " \
        f"Email Address: {self.email_address}. " \
        f"Main Website: {self.main_webpage}, " \
        f"Contact Us Page: {self.contact_us_webpage}. " \
        f"Centre Address: {self.address}."
    