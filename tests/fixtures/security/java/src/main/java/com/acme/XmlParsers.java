package com.acme;

import javax.xml.parsers.DocumentBuilderFactory;

public class XmlParsers {
    public DocumentBuilderFactory unsafe() {
        return DocumentBuilderFactory.newInstance(); // expect: SEC-XXE
    }
}
