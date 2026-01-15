import ReactCountryFlag from "react-country-flag";

export default function CountryFlag({ code }: { code?: string }) {
    if (!code) return null;

    return (
        <ReactCountryFlag
            svg
            countryCode={code}
            style={{ width: "1.2em", height: "1.2em" }}
            title={code}
        />
    );
}