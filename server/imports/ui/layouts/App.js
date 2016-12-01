import React from 'react'
import Head from 'next/head'
import Header from '../components/Header'
import Introduction from '../components/Introduction'
import Content from '../components/Content'
import Footer from '../components/Footer'

export default () => (
  <div>
    <Head>
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/latest/css/bootstrap.min.css" />
      <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css" />
    </Head>
    <Header />
    <Introduction />
    <Content />
    <Footer />
    </div>
)
