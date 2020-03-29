#pragma once

namespace pyfmu
{
    /**
     * @brief Maximal length of log messages. Messages exceeding this length are truncated.
     * 
     */
    constexpr size_t maxLogMessageSize = 1000;

    /**
     * @brief Maximal length of log categories. Categories exceeding this length are truncated.
     * 
     */
    constexpr size_t maxLogCategorySize = 50;
}