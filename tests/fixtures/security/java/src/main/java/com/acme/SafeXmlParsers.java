package com.acme;

import javax.xml.parsers.DocumentBuilderFactory;

public class SafeXmlParsers {
    public DocumentBuilderFactory safe() throws Exception {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        return factory;
    }
}
