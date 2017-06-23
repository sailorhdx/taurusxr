#!/usr/bin/env python
# coding=utf-8
wsdlxml = '<?xml version="1.0" encoding="UTF-8"?>\n<wsdl:definitions targetNamespace="http://www.ly-bns.net/wsdd/" xmlns:apachesoap="http://xml.apache.org/xml-soap" xmlns:impl="http://www.ly-bns.net/wsdd/" xmlns:intf="http://www.ly-bns.net/wsdd/" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/" xmlns:wsdlsoap="http://schemas.xmlsoap.org/wsdl/soap/" xmlns:xsd="http://www.w3.org/2001/XMLSchema">\n\n   <wsdl:message name="userRegResponse">\n\n      <wsdl:part name="userRegReturn" type="soapenc:string"/>\n\n   </wsdl:message>\n\n   <wsdl:message name="userProductModifyRequest">\n\n      <wsdl:part name="nodeId" type="soapenc:string"/>\n\n      <wsdl:part name="userCode" type="soapenc:string"/>\n\n      <wsdl:part name="productCode" type="soapenc:string"/>\n\n      <wsdl:part name="isNext" type="xsd:int"/>\n\n      <wsdl:part name="productChangeFee" type="xsd:int"/>\n\n      <wsdl:part name="operatorCode" type="soapenc:string"/>\n\n      <wsdl:part name="operatorSite" type="soapenc:string"/>\n\n   </wsdl:message>\n\n   <wsdl:message name="userMoveRequest">\n\n      <wsdl:part name="nodeId" type="soapenc:string"/>\n\n      <wsdl:part name="userCode" type="soapenc:string"/>\n\n      <wsdl:part name="areaCode" type="soapenc:string"/>\n\n      <wsdl:part name="courtyardCode" type="soapenc:string"/>\n\n      <wsdl:part name="installAddress" type="soapenc:string"/>\n\n      <wsdl:part name="moveFee" type="xsd:int"/>\n\n      <wsdl:part name="operatorCode" type="soapenc:string"/>\n\n      <wsdl:part name="siteCode" type="soapenc:string"/>\n\n   </wsdl:message>\n\n   <wsdl:message name="userResumeResponse">\n\n      <wsdl:part name="userResumeReturn" type="xsd:int"/>\n\n   </wsdl:message>\n\n   <wsdl:message name="userProductModifyResponse">\n\n      <wsdl:part name="userProductModifyReturn" type="xsd:int"/>\n\n   </wsdl:message>\n\n   <wsdl:message name="userUnRegResponse">\n\n      <wsdl:part name="userUnRegReturn" type="xsd:int"/>\n\n   </wsdl:message>\n\n   <wsdl:message name="userRegRequest">\n\n      <wsdl:part name="nodeId" type="soapenc:string"/>\n\n      <wsdl:part name="userName" type="soapenc:string"/>\n\n      <wsdl:part name="password" type="soapenc:string"/>\n\n      <wsdl:part name="realName" type="soapenc:string"/>\n\n      <wsdl:part name="productCode" type="soapenc:string"/>\n\n      <wsdl:part name="authBeginDate" type="soapenc:string"/>\n\n      <wsdl:part name="authEndDate" type="soapenc:string"/>\n\n      <wsdl:part name="areaCode" type="soapenc:string"/>\n\n      <wsdl:part name="courtyardCode" type="soapenc:string"/>\n\n      <wsdl:part name="installAddress" type="soapenc:string"/>\n\n      <wsdl:part name="ipAddress" type="soapenc:string"/>\n\n      <wsdl:part name="mobile" type="soapenc:string"/>\n\n      <wsdl:part name="idcard" type="soapenc:string"/>\n\n      <wsdl:part name="hasFirstFee" type="xsd:int"/>\n\n      <wsdl:part name="firstFee" type="xsd:int"/>\n\n      <wsdl:part name="installDays" type="xsd:int"/>\n\n      <wsdl:part name="operatorCode" type="soapenc:string"/>\n\n      <wsdl:part name="operatorSite" type="soapenc:string"/>\n\n   </wsdl:message>\n\n   <wsdl:message name="userPauseRequest">\n\n      <wsdl:part name="nodeId" type="soapenc:string"/>\n\n      <wsdl:part name="userCode" type="soapenc:string"/>\n\n      <wsdl:part name="pauseFee" type="xsd:int"/>\n\n      <wsdl:part name="operatorCode" type="soapenc:string"/>\n\n      <wsdl:part name="operatorSite" type="soapenc:string"/>\n\n   </wsdl:message>\n\n   <wsdl:message name="userResumeRequest">\n\n      <wsdl:part name="nodeId" type="soapenc:string"/>\n\n      <wsdl:part name="userCode" type="soapenc:string"/>\n\n      <wsdl:part name="resumeFee" type="xsd:int"/>\n\n      <wsdl:part name="operatorCode" type="soapenc:string"/>\n\n      <wsdl:part name="operatorSite" type="soapenc:string"/>\n\n   </wsdl:message>\n\n   <wsdl:message name="userPauseResponse">\n\n      <wsdl:part name="userPauseReturn" type="xsd:int"/>\n\n   </wsdl:message>\n\n   <wsdl:message name="userUnRegRequest">\n\n      <wsdl:part name="nodeId" type="soapenc:string"/>\n\n      <wsdl:part name="userCode" type="soapenc:string"/>\n\n      <wsdl:part name="currentRefund" type="xsd:int"/>\n\n      <wsdl:part name="nextRefund" type="xsd:int"/>\n\n      <wsdl:part name="operatorCode" type="soapenc:string"/>\n\n      <wsdl:part name="operatorSite" type="soapenc:string"/>\n\n   </wsdl:message>\n\n   <wsdl:message name="userMoveResponse">\n\n      <wsdl:part name="userMoveReturn" type="xsd:int"/>\n\n   </wsdl:message>\n\n   <wsdl:portType name="BusinessGw">\n\n      <wsdl:operation name="userReg" parameterOrder="nodeId userName password realName productCode authBeginDate authEndDate areaCode courtyardCode installAddress ipAddress mobile idcard hasFirstFee firstFee installDays operatorCode operatorSite">\n\n         <wsdl:input message="impl:userRegRequest" name="userRegRequest"/>\n\n         <wsdl:output message="impl:userRegResponse" name="userRegResponse"/>\n\n      </wsdl:operation>\n\n      <wsdl:operation name="userPause" parameterOrder="nodeId userCode pauseFee operatorCode operatorSite">\n\n         <wsdl:input message="impl:userPauseRequest" name="userPauseRequest"/>\n\n         <wsdl:output message="impl:userPauseResponse" name="userPauseResponse"/>\n\n      </wsdl:operation>\n\n      <wsdl:operation name="userMove" parameterOrder="nodeId userCode areaCode courtyardCode installAddress moveFee operatorCode siteCode">\n\n         <wsdl:input message="impl:userMoveRequest" name="userMoveRequest"/>\n\n         <wsdl:output message="impl:userMoveResponse" name="userMoveResponse"/>\n\n      </wsdl:operation>\n\n      <wsdl:operation name="userUnReg" parameterOrder="nodeId userCode currentRefund nextRefund operatorCode operatorSite">\n\n         <wsdl:input message="impl:userUnRegRequest" name="userUnRegRequest"/>\n\n         <wsdl:output message="impl:userUnRegResponse" name="userUnRegResponse"/>\n\n      </wsdl:operation>\n\n      <wsdl:operation name="userProductModify" parameterOrder="nodeId userCode productCode isNext productChangeFee operatorCode operatorSite">\n\n         <wsdl:input message="impl:userProductModifyRequest" name="userProductModifyRequest"/>\n\n         <wsdl:output message="impl:userProductModifyResponse" name="userProductModifyResponse"/>\n\n      </wsdl:operation>\n\n      <wsdl:operation name="userResume" parameterOrder="nodeId userCode resumeFee operatorCode operatorSite">\n\n         <wsdl:input message="impl:userResumeRequest" name="userResumeRequest"/>\n\n         <wsdl:output message="impl:userResumeResponse" name="userResumeResponse"/>\n\n      </wsdl:operation>\n\n   </wsdl:portType>\n\n   <wsdl:binding name="businessgwSoapBinding" type="impl:BusinessGw">\n\n      <wsdlsoap:binding style="rpc" transport="http://schemas.xmlsoap.org/soap/http"/>\n\n      <wsdl:operation name="userReg">\n\n         <wsdlsoap:operation soapAction=""/>\n\n         <wsdl:input name="userRegRequest">\n\n            <wsdlsoap:body encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" namespace="http://www.ly-bns.net/wsdd/" use="encoded"/>\n\n         </wsdl:input>\n\n         <wsdl:output name="userRegResponse">\n\n            <wsdlsoap:body encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" namespace="http://www.ly-bns.net/wsdd/" use="encoded"/>\n\n         </wsdl:output>\n\n      </wsdl:operation>\n\n      <wsdl:operation name="userPause">\n\n         <wsdlsoap:operation soapAction=""/>\n\n         <wsdl:input name="userPauseRequest">\n\n            <wsdlsoap:body encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" namespace="http://www.ly-bns.net/wsdd/" use="encoded"/>\n\n         </wsdl:input>\n\n         <wsdl:output name="userPauseResponse">\n\n            <wsdlsoap:body encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" namespace="http://www.ly-bns.net/wsdd/" use="encoded"/>\n\n         </wsdl:output>\n\n      </wsdl:operation>\n\n      <wsdl:operation name="userMove">\n\n         <wsdlsoap:operation soapAction=""/>\n\n         <wsdl:input name="userMoveRequest">\n\n            <wsdlsoap:body encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" namespace="http://www.ly-bns.net/wsdd/" use="encoded"/>\n\n         </wsdl:input>\n\n         <wsdl:output name="userMoveResponse">\n\n            <wsdlsoap:body encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" namespace="http://www.ly-bns.net/wsdd/" use="encoded"/>\n\n         </wsdl:output>\n\n      </wsdl:operation>\n\n      <wsdl:operation name="userUnReg">\n\n         <wsdlsoap:operation soapAction=""/>\n\n         <wsdl:input name="userUnRegRequest">\n\n            <wsdlsoap:body encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" namespace="http://www.ly-bns.net/wsdd/" use="encoded"/>\n\n         </wsdl:input>\n\n         <wsdl:output name="userUnRegResponse">\n\n            <wsdlsoap:body encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" namespace="http://www.ly-bns.net/wsdd/" use="encoded"/>\n\n         </wsdl:output>\n\n      </wsdl:operation>\n\n      <wsdl:operation name="userProductModify">\n\n         <wsdlsoap:operation soapAction=""/>\n\n         <wsdl:input name="userProductModifyRequest">\n\n            <wsdlsoap:body encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" namespace="http://www.ly-bns.net/wsdd/" use="encoded"/>\n\n         </wsdl:input>\n\n         <wsdl:output name="userProductModifyResponse">\n\n            <wsdlsoap:body encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" namespace="http://www.ly-bns.net/wsdd/" use="encoded"/>\n\n         </wsdl:output>\n\n      </wsdl:operation>\n\n      <wsdl:operation name="userResume">\n\n         <wsdlsoap:operation soapAction=""/>\n\n         <wsdl:input name="userResumeRequest">\n\n            <wsdlsoap:body encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" namespace="http://www.ly-bns.net/wsdd/" use="encoded"/>\n\n         </wsdl:input>\n\n         <wsdl:output name="userResumeResponse">\n\n            <wsdlsoap:body encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" namespace="http://www.ly-bns.net/wsdd/" use="encoded"/>\n\n         </wsdl:output>\n\n      </wsdl:operation>\n\n   </wsdl:binding>\n\n   <wsdl:service name="BusinessGwService">\n\n      <wsdl:port binding="impl:businessgwSoapBinding" name="businessgw">\n\n         <wsdlsoap:address location="{wsurl}/interface/businessgw"/>\n\n      </wsdl:port>\n\n   </wsdl:service>\n\n</wsdl:definitions>'.format